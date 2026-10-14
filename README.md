
## 🚀 Installation & Setup

Follow the steps below to set up and run the project locally on your operating system.

### Prerequisites

* **Python** (version 3.10 or higher recommended) installed on your system.
* **Git** installed to clone the repository.

---

### 1. Clone the Repository

Open your terminal (Linux) or Command Prompt/PowerShell (Windows) and run:

```bash
git clone https://github.com/aluprince/atlas-rag.git
cd atlas-rag

```

---

### 2. Set Up a Virtual Environment

It is recommended to use a virtual environment to manage project dependencies safely without affecting your global Python installation.

#### For Linux / macOS:

```bash
# Create the virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

```

#### For Windows (PowerShell):

```powershell
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1

```

*(Note: If you encounter a script execution permissions error in PowerShell, run `Set-ExecutionPolicy Unrestricted -Scope CurrentUser` first.)*

#### For Windows (Command Prompt):

```cmd
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate.bat

```

---

### 3. Install Dependencies

Once your virtual environment is activated, install the required packages using `pip`:

```bash
pip install --upgrade pip
pip install -r requirements.txt

```

---

### 4. Environment Configuration

Create a `.env` file in the root directory of the project to configure your environment variables and API keys:

```bash
# Linux / macOS / Windows (Git Bash)
touch .env

```

*(On Windows Command Prompt, you can create it via `type nul > .env` or using your preferred code editor like VS Code).*

Open the `.env` file and add your required configuration details (e.g., API keys, database URLs):

```env
# Example .env configuration
API_KEY=your_api_key_here

```

---

### 5. Run the Application

Start your application using your entry point script (e.g., FastAPI or main runner):

```bash
python main.py

```

*(Or if using Uvicorn directly)*:

```bash
uvicorn main:app --reload

```
