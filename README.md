# 🏍️ Road Log Moto — Diário de Bordo & PWA (Viagem Piódão)

Aplicação Web Progressiva (PWA) de alta performance, desenhada especificamente para suporte de guiador de moto (Quad Lock, RAM Mount, SP Connect) ou utilização rápida na berma da estrada com luvas.

🌐 **Acesso Online (GitHub Pages)**: [https://rpmariano.github.io/log_book/](https://rpmariano.github.io/log_book/)

---

## 📱 Como Instalar no Telemóvel (100% Offline)

A app funciona como uma aplicação nativa no teu smartphone e **continua a funcionar sem qualquer rede móvel** (mesmo nas zonas sem cobertura da Serra do Açor, Fajão e Piódão):

### No iPhone (Safari):
1. Abre [https://rpmariano.github.io/log_book/](https://rpmariano.github.io/log_book/) no **Safari**.
2. Toca no botão de **Partilhar** (ícone quadrado com a seta para cima na barra inferior).
3. Seleciona **"Ecrã Principal"** (ou *"Adicionar ao Ecrã Principal"*).
4. O ícone 🏍️ surge no ecrã do teu iPhone e abre em ecrã inteiro sem barras de browser!

### No Android (Chrome):
1. Abre [https://rpmariano.github.io/log_book/](https://rpmariano.github.io/log_book/) no **Chrome**.
2. Toca no menu dos **3 pontinhos** no canto superior direito.
3. Escolhe **"Instalar aplicação"** ou **"Adicionar ao ecrã inicial"**.
4. A app fica instalada e funciona como app nativa.

---

## ✨ Funcionalidades Pensadas para a Mota

1. **Ergonomia com Luvas & Thumb-Zone**:
   - Barra de navegação inferior acessível diretamente com o polegar.
   - Botões gigantes táteis (mínimo de 52px de altura) com feedback de vibração háptica.
   - **Modo Sol (Alto Contraste)**: Botão no topo para alternar entre Dark Mode e modo de luminosidade máxima para sol direto de verão/outono.

2. **Cockpit do Momento**:
   - Exibe a etapa ativa com quilometragem, tempo previsto e tipo de estrada.
   - Botões diretos para iniciar navegação em **Google Maps** (com paragens intermédias calculadas) ou **Waze**.
   - Cronograma com indicação automática de **AGORA** e **A SEGUIR**.

3. **Diário de Bordo Rápido (Road Log)**:
   - **Ditado por Voz (Speech-to-Text)**: Toca no microfone e fala a nota diretamente pelo intercomunicador do capacete ou telemóvel.
   - **Chips Rápidos**: Regista com 1 toque (*"⛽ Abastecimento"*, *"☕ Café"*, *"🍽️ Almoço"*, *"📸 Foto"*, *"⚠️ Alerta"*).
   - **Suporte Multimédia (Fotos & Vídeos)**: Fotos com compressão instantânea e upload de pequenos clips de vídeo.
   - **Offline-First com Sincronização Supabase**: Guarda sempre primeiro no telemóvel (`localStorage`), sincronizando com a base de dados quando houver rede.

4. **SOS & Coordenadas em Letra Gigante**:
   - Latitude e longitude exatas com precisão em metros e texto de alto contraste para ditar por chamada.
   - Botão para **Copiar Coordenadas** com 1 toque.
   - Chamada direta para o **112** e **SNS 24 (808 24 24 24)**.
   - Calculadora de autonomia e abastecimento.

5. **GPS & Meteorologia**:
   - Mapa interativo Leaflet com traçados de cada dia, postos de combustível críticos e botão de radar *"Onde estou?"*.
   - Previsão de temperatura, probabilidade de chuva e vento nas paragens à hora prevista.
   - Exportação de ficheiros **GPX** para GPS de moto (Garmin Zumo, TomTom Rider, BMW Motorrad Connected, OsmAnd).
