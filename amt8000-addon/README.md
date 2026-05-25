# Home Assistant Add-on: AMT-8000 Alarm Manager

Este add-on permite conectar, monitorar e gerenciar a central de alarmes **Intelbras AMT-8000** diretamente pelo Home Assistant, utilizando uma interface web moderna, interativa e totalmente integrada via Ingress.

O add-on utiliza o protocolo **iSEC2** para estabelecer uma conexão TCP bidirecional e segura com a central física de alarmes, oferecendo controle em tempo real sem depender de serviços em nuvem.

---

## 🚀 Recursos Principais

- **Visualização Completa do Status**:
  - Estado geral do sistema (Armado Total, Armado Parcial, Desarmado, Disparado).
  - Informações de até **16 partições** (Ativa, Armada, Modo Stay, Disparada).
  - Informações de todas as **64 zonas** (Ativa, Aberta/Fechada, Violada, Anulada/Bypassed, Bateria Fraca, Tamper).
  - Diagnóstico da central (Nível da bateria da central, IP, Porta, Versão do Firmware e última atualização).
- **Controle Total**:
  - Arme e desarme de partições individuais.
  - Arme ou desarme global (todas as partições ativas de uma só vez).
  - **Anulação (Bypass) de Zonas**: Permite isolar zonas diretamente pelo painel web.
  - **Disparos de Pânico**: Botão dedicado para acionamento de Pânico Sonoro ou Pânico Silencioso.
- **Interface Premium**:
  - Design moderno com efeito de vidro (*glassmorphism*) e modo escuro nativo.
  - Otimizado para telas de computadores, tablets e dispositivos móveis (design responsivo).
  - Atualizações e animações fluidas em tempo real.
  - Suporte completo ao **Home Assistant Ingress** (exibição direta no menu lateral do HA).

---

## 🔌 Pré-requisitos

1. **Configuração da Central AMT-8000**:
   - A central deve estar conectada à sua rede local (via Ethernet ou Wi-Fi).
   - O serviço de receptores ou conexões IP deve estar ativo na central (geralmente porta `9009`).
   - Você precisará de uma **senha de usuário numérica de 6 dígitos** cadastrada na central com permissão de arme/desarme.

---

## 🛠️ Instalação

1. No seu Home Assistant, navegue até **Configurações** -> **Add-ons** -> **Loja de Add-ons**.
2. Clique no menu de três pontos no canto superior direito e selecione **Repositórios**.
3. Adicione a URL do seu repositório de add-ons e clique em salvar.
4. Localize o **AMT-8000 Alarm Manager** na lista e clique em **Instalar**.
5. Aguarde a conclusão da instalação.

---

## ⚙️ Configuração

Navegue até a guia **Configuração** do Add-on no Home Assistant para preencher os seguintes campos obrigatórios:

```yaml
host: "192.168.1.100"      # O endereço IP da sua central na rede local
port: 9009                 # A porta TCP configurada na central (padrão: 9009)
password: "123456"         # Senha numérica de 6 dígitos de um usuário da central
update_interval: 4         # Intervalo de consulta à central em segundos (padrão: 4)
```

### Detalhes das Opções:

- **`host`** (obrigatório): O endereço de IP da sua central Intelbras AMT-8000. Recomendamos configurar um IP estático ou reserva de DHCP no seu roteador para a central.
- **`port`** (obrigatório): Porta TCP de comunicação. O padrão de fábrica da Intelbras é `9009`.
- **`password`** (obrigatório): Uma senha numérica válida de 6 dígitos cadastrada na central.
- **`update_interval`** (opcional): O tempo de espera entre cada atualização de status. O valor mínimo é `1` segundo e o máximo é `300` segundos. O padrão recomendado é `4` segundos.

---

## 🚦 Executando o Add-on

1. Retorne à guia **Informações** do Add-on.
2. Ative as opções **Iniciar na inicialização** e **Mostrar na barra lateral** (para habilitar o acesso rápido via Ingress no menu esquerdo).
3. Clique em **Iniciar**.
4. Acompanhe os logs na guia **Logs** para garantir que a conexão com a central foi estabelecida com sucesso.
5. Clique em **Abrir Interface Web** para acessar o painel de gerenciamento completo.

---

## 📝 Changelog

Consulte o arquivo [CHANGELOG.md](file:///c:/Users/alexa/Desktop/AMT8000/Alarme-AMT8000/amt8000-addon/CHANGELOG.md) para ver o histórico de atualizações e novas implementações.
