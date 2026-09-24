# 🏍️ Road Log Moto — Viagem Piódão & Aldeias do Xisto

Aplicação mobile de alta performance desenhada especificamente para suporte de guiador de moto (Quad Lock, RAM Mount, SP Connect) ou utilização rápida na berma da estrada com luvas.

---

## 🚀 Como Usar no Telemóvel

### Opção 1: Abrir Imediatamente como App Nativa (PWA) — Recomendado!
1. Abre o ficheiro `index.html` no browser do teu telemóvel (Safari no iPhone ou Chrome no Android).
2. **No iPhone (Safari)**: Toca no botão de **Partilhar (quadrado com seta para cima)** → Escolhe **"Adicionar ao Ecrã Principal"**.
3. **No Android (Chrome)**: Toca nos 3 pontinhos no topo direito → Escolhe **"Instalar Aplicação"** ou **"Adicionar ao ecrã principal"**.
4. A app fica instalada com o ícone 🏍️, abre em ecrã inteiro (sem barras de browser) e **funciona 100% offline**, mesmo nos vales sem qualquer rede móvel na Serra do Açor, Fajão e Piódão!

*(Dica: Podes colocar a pasta no GitHub Pages, Vercel, Netlify ou enviar o ficheiro `index.html` para ti mesmo por WhatsApp / AirDrop).*

---

### Opção 2: Correr a Versão Streamlit Modernizada
Se preferires correr a versão Python no computador ou alojar no Streamlit Community Cloud:
```bash
pip install streamlit folium streamlit-folium requests pillow
streamlit run app_streamlit.py
```

---

## ✨ Funcionalidades Pensadas para a Mota

1. **Ergonomia com Luvas & Thumb-Zone**:
   - Barra de navegação inferior acessível diretamente com o polegar.
   - Botões gigantes táteis (mínimo de 52px de altura) com feedback de vibração háptica.
   - **Modo Sol (Alto Contraste)**: Botão no topo para alternar entre Dark Mode e modo de luminosidade máxima para sol direto de verão/outono.

2. **Cockpit do Momento**:
   - Exibe a etapa ativa com quilometragem, tempo previsto e tipo de estrada (Autoestrada vs Curvas/Nacionais).
   - Botões diretos para iniciar navegação em **Google Maps** (com paragens intermédias calculadas) ou **Waze**.
   - Cronograma com indicação automática de **AGORA** e **A SEGUIR**.

3. **Diário de Bordo Rápido (Road Log)**:
   - **Ditado por Voz (Speech-to-Text)**: Toca no microfone e fala a nota diretamente pelo intercomunicador do capacete ou telemóvel.
   - **Chips Rápidos**: Regista com 1 toque (*"⛽ Abastecimento"*, *"☕ Café"*, *"🍽️ Almoço"*, *"📸 Foto"*, *"⚠️ Alerta"*).
   - **Compressão Instantânea de Fotos**: As fotos da câmara são automaticamente reduzidas no telemóvel para ~200KB antes de guardar, poupando bateria e funcionando mesmo em 2G/EDGE.
   - **Offline-First com Sincronização Supabase**: Guarda sempre primeiro no telemóvel (`localStorage`), sincronizando com a tua base de dados na nuvem assim que recuperares rede móvel.

4. **SOS & Coordenadas em Letra Gigante**:
   - Mostra a latitude e longitude exatas com precisão em metros.
   - Botão para **Copiar Coordenadas** e enviar por SMS/WhatsApp em caso de avaria.
   - Chamada direta com 1 toque para o **112** e **SNS 24 (808 24 24 24)**.
   - Calculadora rápida de abastecimento e autonomia.

5. **GPS & Meteorologia**:
   - Mapa interativo Leaflet com traçados de cada dia, postos de combustível críticos e botão *"Onde estou?"* com radar de localização.
   - Previsão de temperatura, probabilidade de chuva e vento nas paragens à hora prevista.
   - Exportação de ficheiros **GPX** para GPS de moto (Garmin Zumo, TomTom Rider, BMW Motorrad Connected, OsmAnd).
