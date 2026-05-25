# Changelog

## [1.3.2] - 2026-05-25

### Corrigido
- Inclusão de cabeçalhos HTTP estritos de expiração e controle de cache (`Cache-Control: no-store, no-cache, must-revalidate`, `Pragma: no-cache`, `Expires: 0`) especificamente no retorno da rota principal `/` que renderiza o arquivo `index.html`. Isso força o Service Worker e os navegadores integrados ao Home Assistant Ingress a recarregarem sempre a página HTML original atualizada contendo os parâmetros de cache-busting `?v=1.3.2` nos scripts e layouts, em vez de continuarem exibindo a versão antiga de layout armazenada no cache persistente offline do aplicativo.

## [1.3.1] - 2026-05-25

### Corrigido
- Remoção do caractere `?` das chaves de schema de `zones` e `partitions` no `config.yaml`. Isso resolve o erro de validação do Home Assistant Supervisor (`Missing option 'zones?' in root`), que tentava ler o caractere do sufixo como parte literal do nome da propriedade em vez de uma marcação opcional.

## [1.3.0] - 2026-05-25

### Adicionado
- Recurso de **Nomes Personalizados de Zonas e Partições**:
  - Adicionado suporte no `config.yaml` e no formulário de configurações do Home Assistant para configurar listas opcionais de zonas e partições com nomes personalizados (ex: `número: 6, nome: Sala de Estar`).
  - Atualização do `server.py` para ler automaticamente o arquivo de opções `/data/options.json` fornecido pelo Home Assistant e aplicar o mapeamento de nomes de forma dinâmica nas respostas da API REST `/api/status`.
  - Atualização do `app.js` no frontend para exibir os nomes customizados de zonas e partições nas respectivas cartas do dashboard (mantendo fallback automático para os nomes de fábrica "Zona XX" e "Partição XX").
  - Aprimoramento da ferramenta de pesquisa de zonas na interface web: agora a busca filtra zonas tanto por número quanto pelos seus nomes customizados (ex: pesquisar "Sala" trará as zonas personalizadas correspondentes).
  - Adicionadas traduções completas de descrição e rotulagem para a interface de configuração em Português (`pt.yaml`) e Inglês (`en.yaml`).

## [1.2.3] - 2026-05-25

### Melhorado
- Telemetria de sensores sem fio aprimorada com display mais rico e informativo:
  - Bateria do sensor agora mostra estimativa percentual explícita: `Bat. OK (100%)` (quando a bateria está normal) e `Bat. Fraca (10%)` (quando em nível crítico/fraco).
  - Sinal sem fio agora exibe rótulo intuitivo: `Sinal Forte` (em vez do genérico Sinal OK) e `Sem Sinal` (em vez de Sinal Ruim) baseado no estado de supervisão do sensor.

## [1.2.2] - 2026-05-25

### Corrigido
- Ajuste de layout em `style.css` definindo `.toggle-switch` com `display: inline-block`, o que evita o colapso de dimensões do label de toggle na tela e corrige o bug visual que deslocava e cortava a chave de bypass para fora do limite das cartas de zonas.
- Aumento da opacidade e refinamento estético do fundo da barra deslizante do bypass (`rgba(255,255,255,0.08)`) para visibilidade premium do switch.
- Solução de condição de corrida (race condition) de atualização do estado da interface: agora os comandos de Armar, Desarmar, Bypass e Unbypass alteram instantaneamente o cache de status local em memória do servidor Flask. Isso elimina o comportamento jumpy (onde a chave ligava e voltava imediatamente para desligado até a próxima varredura de polling em background da central física).

## [1.2.1] - 2026-05-25

### Corrigido
- Correção do comando de Bypass (anulação) e Unbypass (reativação) de zonas, mudando o código do comando do incorreto `401C` para o código oficial da central `401F` (`COMMANDS["bypass"] = [0x40, 0x1F]`).
- Ajuste no índice das zonas nos comandos de Bypass/Unbypass para formato 0-indexed (`zone_number - 1`), alinhando com a especificação da central AMT-8000 e resolvendo a rejeição silenciosa de comandos.
- Implementação de tratamento explícito de pacotes de rejeição NAK (`0xFD`) da central de alarme para reportar falhas de comandos corretamente de forma síncrona.
- Introdução de parâmetros dinâmicos de cache-busting (`?v={{ version }}`) nos links de folhas de estilo CSS e scripts JS, garantindo que o Home Assistant Ingress atualize a interface web imediatamente após atualizações do add-on, resolvendo problemas onde a telemetria não aparecia na tela por cache antigo do navegador.

## [1.2.0] - 2026-05-25

### Adicionado
- Telemetria de bateria e sinal sem fio para sensores sem fio (zonas) no painel web, implementando um display premium de ícones e badges dinâmicas baseadas nos bits de `lowBattery` (bateria do sensor) e `tamper` (que sinaliza integridade/perda de supervisão do sensor).

## [1.1.0] - 2026-05-25

### Corrigido
- Ajuste e correção do critério de sucesso do comando de Bypass (anulação) e Unbypass (reativação) de zonas, adicionando suporte à validação do byte de resultado `0xFE` no índice 8 (`res_byte == 0xFE`), que é o retorno real de sucesso emitido pela central AMT-8000 para estas operações.

## [1.0.9] - 2026-05-25

### Adicionado
- Logs verbosos de diagnóstico detalhados para as operações de Armar, Desarmar, Pânico, Bypass (anulação) e Unbypass (reativação) de zonas, exibindo comandos enviados e respostas recebidas em formato hexadecimal.

### Corrigido
- Implementação de salvaguarda de limites de índice (proteção contra `IndexError`) em todas as respostas de comandos de rede da central de alarme, evitando falhas silenciosas do servidor caso a central responda com pacotes curtos ou malformados.

## [1.0.8] - 2026-05-25

### Corrigido
- Correção de bug crítico de cálculo off-by-one no tamanho total do pacote de dados (`_read_data`), mudando de `8 + expected_len` para `7 + expected_len` bytes. Isso resolve de forma definitiva o problema de timeout infinito gerado pela leitura de um byte extra inexistente após o checksum.

## [1.0.7] - 2026-05-25

### Adicionado
- Logs verbosos de diagnóstico para o fluxo de conexão TCP do socket, comandos de autenticação em formato hexadecimal e loop de recebimento e fragmentação de pacotes iSEC2 para identificar timeouts.

## [1.0.6] - 2026-05-25

### Corrigido
- Desativação do perfil AppArmor (`apparmor: false`) no `config.yaml` para remover as restrições de segurança do contêiner sobre soquetes TCP de rede, permitindo conectividade irrestrita com a rede física local.

## [1.0.5] - 2026-05-25

### Corrigido
- Alteração da porta do Ingress e do servidor Flask de `8099` para `8199` para resolver conflito de endereço já em uso ("Address in use") ao rodar no modo de rede do host.

## [1.0.4] - 2026-05-25

### Corrigido
- Ativação de `host_network: true` no `config.yaml` para permitir que o add-on acesse diretamente a rede local (LAN) do host, evitando timeouts causados por isolamento de rede do Docker bridge.

## [1.0.3] - 2026-05-25

### Corrigido
- Configuração de `init: false` no `config.yaml` para desativar o wrapper tini e permitir que o s6-overlay do contêiner execute como PID 1 sem conflitos.

## [1.0.2] - 2026-05-25

### Corrigido
- Inclusão da cópia explícita do script `run.sh` no Dockerfile para corrigir falha de compilação da imagem Docker.

## [1.0.1] - 2026-05-25

### Corrigido
- Remoção da chave de download de imagem `image` para forçar a compilação local a partir do Dockerfile.
- Correção da arquitetura depreciada `armv7` para `armhf` no arquivo de configuração do add-on.

## [1.0.0] - 2026-05-25

### Adicionado
- Versão inicial do Add-on **AMT-8000 Alarm Manager**.
- Cliente do protocolo **iSEC2** robusto e adaptado, com suporte multi-thread e bloqueio de concorrência.
- API REST em Flask integrada para comunicação bidirecional de status e comandos com a central.
- Suporte nativo ao **Home Assistant Ingress** para integração no menu lateral.
- Painel de gerenciamento web moderno com design *glassmorphism* e tema escuro premium.
- Suporte a monitoramento de até **16 partições** e **64 zonas** ativas.
- Implementação de **Bypass de Zonas** (anulação temporária de zonas diretamente no painel).
- Botões de **Pânico** (Audível e Silencioso).
- Filtros inteligentes e sistema de busca em tempo real na listagem de zonas.
- Badges de diagnósticos (nível de bateria da central, firmware, IP e porta).
- Arquivos de tradução em Português (`pt.yaml`) e Inglês (`en.yaml`) para a tela de configurações do Home Assistant.
- Arte de ícone e logo geradas exclusivamente para identidade visual refinada do add-on.
