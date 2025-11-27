@echo off
echo 🚀 Setting up Chat App Conda Environment...

conda env create -f environment.yml
conda activate chatapp_env

echo ✅ Conda setup complete!
echo 💡 Activate environment with: conda activate chatapp_env
echo 💻 Run server with: cd server && python main.py
echo 💻 Run client with: cd client && python main.py
echo 📊 Launch Jupyter: jupyter lab