# SETUP.md — RunTechOps

Guia passo a passo para configurar o ambiente do RunTechOps pela primeira vez (ou recriar após mover a pasta). Estimativa: **30-40 minutos** se tudo correr bem.

> ⚠️ **Antes de começar:** este setup vai mexer com credenciais. Reserve um momento sem interrupção.

---

## 📋 Visão geral dos 8 passos

| # | Passo | Tempo |
|---|---|---|
| 1 | Trocar senha do Garmin (segurança crítica) | 5 min |
| 2 | Verificar Python instalado | 1 min |
| 3 | Abrir PowerShell na pasta RunTechOps | 1 min |
| 4 | Criar virtual environment (`.venv`) | 1-2 min |
| 5 | Ativar o venv | 30 s |
| 6 | Instalar dependências (`pip install -r requirements.txt`) | 3-8 min |
| 7 | Criar `.env` com credenciais | 2 min |
| 8 | Testar `conn.py` e `dashboard.py` | 2-3 min |

---

## 🔴 Passo 1 — Trocar a senha do Garmin (CRÍTICO)

**Por quê:** a senha antiga (`!Q2w3e4r@`) ficou em texto plano no `conn.py` original em `C:\Python\Garmin\` por meses. Pode estar comprometida. Troque agora.

### Como fazer

1. Acesse [https://connect.garmin.com](https://connect.garmin.com).
2. Login com email atual (`osilvajr@gmail.com`).
3. Canto superior direito → ícone de perfil → **"Conta"** → **"Configurações da conta"**.
4. Aba **"Segurança"** → **"Alterar senha"**.
5. Crie senha **NOVA, FORTE e ÚNICA** (não usar em outros serviços):
   - Mínimo 12 caracteres
   - Letras maiúsculas + minúsculas + números + símbolos
   - **Sugestão de gerador:** Bitwarden, 1Password, ou mesmo `Get-Random` no PowerShell
6. **Anote a senha em local seguro** (gerenciador de senhas).

### ⚠️ Verificar exposição cruzada

Se a senha antiga era usada em outros serviços, **trocar todos**:
- [ ] Gmail (se for igual)
- [ ] TrainingPeaks
- [ ] Strava (se usar)
- [ ] Outros sites

> 💡 **Dica:** ao terminar, faça login em [haveibeenpwned.com](https://haveibeenpwned.com) com seu email para checar vazamentos conhecidos.

---

## 🐍 Passo 2 — Verificar Python instalado

### Como verificar

Abra o **PowerShell** (Windows + R → digite `powershell` → Enter) e rode:

```powershell
python --version
```

### Resultados esperados

| Saída | O que significa | Ação |
|---|---|---|
| `Python 3.10.x` ou superior | ✅ OK | Próximo passo |
| `Python 3.9.x` ou inferior | 🟡 Funciona, mas atualize | Instalar 3.11 ou 3.12 |
| `Python 2.7.x` | ❌ Muito antigo | Instalar 3.11 ou 3.12 |
| `'python' não é reconhecido...` | ❌ Não instalado | Instalar 3.11 ou 3.12 |

### Como instalar Python (se necessário)

1. Baixe em [python.org/downloads](https://www.python.org/downloads/).
2. **IMPORTANTE:** marcar **"Add Python to PATH"** no instalador.
3. Reiniciar o PowerShell e testar `python --version` de novo.

---

## 📂 Passo 3 — Abrir PowerShell na pasta RunTechOps

### Como fazer

```powershell
cd "C:\_Dados\OneDrive - GS Comercio Internacional\Jr\Pesq_Jr\RunTechOps"
```

### Verificar que está no lugar certo

```powershell
ls
```

Você deve ver:
```
.env.example
.gitignore
README.md
SETUP.md          (este arquivo)
conn.py
dashboard.py
garmin_activity_data.csv
lastrun.py
lastrun_log.txt
requirements.txt
Atividades Baixadas/
```

> 💡 **Atalho:** no Explorer, navegue até a pasta, clique na barra de endereços, digite `powershell` e Enter — abre direto no caminho.

---

## 🏗️ Passo 4 — Criar virtual environment (`.venv`)

**Por quê:** isola as dependências deste projeto do Python global do sistema. Evita conflitos.

### Comando

```powershell
python -m venv .venv
```

### Verificar

Após rodar, deve aparecer uma pasta `.venv/` na pasta atual:

```powershell
ls .venv
```

Saída esperada:
```
Include
Lib
pyvenv.cfg
Scripts
```

### Possíveis erros

| Erro | Solução |
|---|---|
| `python: can't open file 'venv'` | Rode com `-m`: `python -m venv .venv` (com hífen) |
| `Error: [Errno 13] Permission denied` | Feche o VSCode/Explorer apontando para a pasta e tente de novo |
| Lentidão extrema (>5 min) | Possível antivírus escaneando — pausar temporariamente |

---

## 🔌 Passo 5 — Ativar o virtual environment

### Comando

```powershell
.\.venv\Scripts\Activate.ps1
```

### Verificar ativação

O prompt do PowerShell muda para começar com `(.venv)`:

```
(.venv) PS C:\_Dados\OneDrive - GS Comercio Internacional\Jr\Pesq_Jr\RunTechOps>
```

### Erro comum: ExecutionPolicy

Se aparecer:
```
... cannot be loaded because running scripts is disabled on this system.
```

**Solução** (rodar uma vez por usuário, é seguro):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Confirme com `S` (Sim). Tente ativar de novo.

> 🔄 **Importante:** o venv precisa ser ativado **toda vez** que abrir um PowerShell novo para trabalhar no RunTechOps. Para sair: `deactivate`.

---

## 📦 Passo 6 — Instalar dependências

### Comando

```powershell
python -m pip install -r requirements.txt
```

> ⚠️ **Use `python -m pip`, não só `pip`.** Pegadinha real do Windows + Python 3.13: às vezes o `.venv` não cria um `pip.exe` próprio em `.venv\Scripts\`. Aí `pip` aponta pro pip global e instala fora do venv. Usar `python -m pip` força o pip do Python ativo (do venv).

### O que vai instalar

- `garminconnect` — cliente Garmin Connect
- `python-dotenv` — leitor de `.env`
- `pandas`, `numpy`, `python-dateutil` — análise de dados
- `streamlit`, `altair`, `folium`, `streamlit-folium`, `branca`, `matplotlib`, `pydeck` — dashboard

**Tempo estimado:** 3-8 min (dependendo da internet). É o passo mais lento.

### Verificar instalação

```powershell
pip list
```

Deve listar todos os pacotes acima.

### Possíveis erros

| Erro | Solução |
|---|---|
| `ERROR: pip's dependency resolver does not currently take...` | Aviso, não erro — pode ignorar |
| `ERROR: Could not find a version that satisfies the requirement` | Internet caiu ou pacote indisponível — tentar de novo |
| `ERROR: Microsoft Visual C++ 14.0 is required` | Instalar [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/) |
| Lentidão | Use mirror: `pip install -r requirements.txt -i https://pypi.org/simple/` |

---

## 🔐 Passo 7 — Criar arquivo `.env` com credenciais

**O `.env` guarda email e senha do Garmin. Ele NUNCA é commitado em git** (já está no `.gitignore`).

### Comando para criar

```powershell
copy .env.example .env
```

### Editar com Notepad

```powershell
notepad .env
```

### Conteúdo a preencher

Substituir os valores de exemplo pelos reais:

```env
# Credenciais Garmin Connect — copie este arquivo para .env e preencha
# NUNCA commit o .env em git. Veja .gitignore.

GARMIN_EMAIL=osilvajr@gmail.com
GARMIN_PASSWORD=SUA_SENHA_NOVA_DO_PASSO_1

# === Opcional (futuro) ===

# Notificações Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Caminho local do CSV exportado do TrainingPeaks
TP_CSV_PATH=./tp_export/workouts.csv
```

> ⚠️ **Atenção:**
> - **Sem aspas** em volta da senha (a menos que ela contenha `#`).
> - **Sem espaços** em torno do `=`.
> - **Não deixe** a senha "padrão" do `.env.example` se for igual à sua.

### Salvar e fechar

`Ctrl+S` no Notepad → fechar.

### Verificar

```powershell
type .env
```

Deve mostrar o conteúdo. Confirme que email + senha estão corretos.

---

## 🧪 Passo 8 — Testar o RunTechOps

### 8a) Teste de conexão (`conn.py`)

```powershell
python conn.py
```

#### Saída esperada (✅ sucesso)

```
--- Dados de 2026-05-XX ---
Passos totais: 7234
FC Repouso: 51 bpm
Stress medio: 22
Body Battery min/max: 41 / 78

Atividades de hoje:
  - Caminhada | 1.85 km | 25 min
```

#### Possíveis erros

| Erro | Causa | Solução |
|---|---|---|
| `ERRO: configure GARMIN_EMAIL e GARMIN_PASSWORD no arquivo .env` | `.env` não foi criado ou está vazio | Voltar ao Passo 7 |
| `Erro ao conectar: Authentication failed` | Senha errada no `.env` | Conferir senha (caps lock?) |
| `Erro ao conectar: Too many failed login attempts` | Garmin bloqueou temporariamente | Esperar 30 min, tentar de novo |
| `ModuleNotFoundError: No module named 'garminconnect'` | Venv não ativado ou install não rodou | Voltar ao Passo 5 e 6 |
| `Erro: Connection error` | Internet ou Garmin fora do ar | Testar [https://connect.garmin.com](https://connect.garmin.com) no navegador |
| `MFA / 2FA prompt` | Garmin com 2FA ativado | Desabilitar 2FA temporariamente OU usar `garth` (futuro) |

### 8b) Teste do dashboard (`dashboard.py`)

```powershell
streamlit run dashboard.py
```

#### Saída esperada

```
You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

O navegador abre automaticamente em `http://localhost:8501`.

#### O que testar no dashboard

1. Selecionar um arquivo TCX da pasta `Atividades Baixadas/` (qualquer treino antigo serve).
2. Verificar se aparece:
   - Mapa com o trajeto
   - Gráfico de FC com **suas zonas Karvonen** (cores Z1-Z5)
   - Pace, distância, cadência
3. Fechar com `Ctrl+C` no PowerShell quando terminar.

#### Possíveis erros

| Erro | Solução |
|---|---|
| `ModuleNotFoundError: No module named 'streamlit'` | Venv não ativado |
| `Port 8501 is already in use` | Outro Streamlit rodando — mudar porta: `streamlit run dashboard.py --server.port 8502` |
| Mapa não aparece | TCX sem GPS — tentar outro arquivo |
| Zonas FC erradas | Conferir `FC_MAX = 170` e `FC_REP = 51` no `dashboard.py` (linhas ~286-296) |

### 8c) (Opcional) Baixar atividades novas (`lastrun.py`)

```powershell
python lastrun.py
```

Ele pergunta quantas atividades baixar. Tente `5` para testar. Verifica em `Atividades Baixadas/`.

---

## ✅ Verificação final

Ao terminar, você deve ter:

- [ ] Senha do Garmin trocada e anotada em local seguro
- [ ] Pasta `.venv/` criada e ativada
- [ ] Todas as dependências instaladas (`pip list` mostra ~12 pacotes)
- [ ] `.env` criado com credenciais corretas
- [ ] `python conn.py` retorna dados do Garmin sem erro
- [ ] `streamlit run dashboard.py` abre o dashboard no navegador
- [ ] Pasta `C:\Python\Garmin\` — **NÃO deletar ainda** (só após confirmar RunTechOps 100% OK por alguns dias de uso)

---

## 🔄 Uso no dia a dia (após setup pronto)

Toda vez que for usar o RunTechOps:

```powershell
cd "C:\_Dados\OneDrive - GS Comercio Internacional\Jr\Pesq_Jr\RunTechOps"
.\.venv\Scripts\Activate.ps1

# Agora pode rodar:
python conn.py                # checagem rápida
python lastrun.py             # baixar TCXs novos
streamlit run dashboard.py    # dashboard de TCX
python health_daily.py        # snapshot de saúde do dia (gera dash.html ao final)
python dash_today.py          # painel HTML do dia (HRV, BB, FCrep, Sleep + veredito)

# Ao terminar:
deactivate
```

---

## 🐛 Troubleshooting geral

### "Esqueci de ativar o venv e instalei pacotes no Python global"

Sem problema. Ative o venv (Passo 5) e rode `python -m pip install -r requirements.txt` de novo dentro dele.

### "Quero recomeçar o setup do zero"

```powershell
deactivate                # se venv estiver ativo
rm -r .venv               # apaga venv
rm .env                   # apaga credenciais
# Voltar ao Passo 4
```

### "O `.env` foi commitado por engano em git"

1. **Trocar a senha do Garmin imediatamente** (Passo 1 de novo).
2. Remover do histórico:
   ```powershell
   git rm --cached .env
   git commit -m "remover .env do histórico"
   ```
3. Confirmar que `.gitignore` contém `.env`.

### "Quero testar `conn.py` mas não tenho internet"

Não dá — `conn.py` precisa conectar ao Garmin Connect. Use o `dashboard.py` que funciona offline com TCXs locais.

---

## 🎯 Próximos passos depois deste setup

Conforme `project_runtechops.md`:

1. **Após 12/05/2026** (HRV diário começando) → criar `health_daily.py`
2. **Após 19/05/2026** → criar `pmc.py` + `tp_import.py`
3. **Após 24/05/2026** (baseline HRV pronta) → criar `scoring.py` + SQLite + Telegram + agendamento

Mas isso é depois. Primeiro, este setup.

---

*SETUP.md criado em 06/05/2026. Atualizado em 06/05/2026 após migração para `RunTechOps/`.*
