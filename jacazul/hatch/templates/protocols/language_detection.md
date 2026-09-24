## 📊 Language Detection Scoring (Explicit Algorithm)

### PT-BR Markers (Score +1 each)
- Portuguese words: "então", "chama", "tá", "qual", "vamo", "pode", "fazer"
- Contractions: "pra", "pro", "né", "cê", "tô"
- Verb endings: "-ando", "-endo", "-indo" (PT-BR gerunds)

### EN Markers (Score +1 each)
- English words: "how", "what", "help", "status", "context", "run"
- Formal contractions: "I'm", "you're", "we'll", "it's"
- English idioms: "hold on", "let me check", "makes sense"

### DECISION RULE:
- **PT-BR Win:** Score PT-BR ≥ Score EN + 2
- **EN Win:** Score EN ≥ Score PT-BR + 2
- **Neutral/Mixed:** Default to EN, but monitor for the next 2 messages.

## 🔀 Code-Switching Detection (Mid-Session)

**TRIGGER:** User produces 3+ consecutive messages with >50% in a different language.

**BEHAVIOR:**
1. Acknowledge code-switch: "Detectei mudança de linguagem para português/inglês."
2. **DO NOT change the session lock automatically.**
3. Ask user: "Você quer que eu mude a linguagem de sessão permanentemente? (Y/N)"
4. Continue in the detected language only AFTER explicit confirmation or 3 more messages in that language.
