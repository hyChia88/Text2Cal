https://text2cal.vercel.app/

Running the Frontend (Next.js)
```
cd /path/to/your/project

# Install dependencies (if you haven't already)
npm install

# Start the development server
npm run dev
```
The frontend should start and be accessible at http://localhost:3000

Running the Backend (Flask)
```
cd /path/to/your/project/backend

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies (if you haven't already)
pip install -r requirements.txt  # If you have a requirements file
# Or install manually:
pip install flask requests flask-cors openai python-dotenv

# Start the Flask server
python app.py
```
The backend should start and be accessible at http://localhost:5000