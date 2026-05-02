# 🤖 LLM Code Analyzer - Streamlit App

A **beast UI** for AI-powered code analysis built with Streamlit! This modern web interface provides an intuitive way to analyze your code using multiple LLM models with advanced features like RAG, performance profiling, and security scanning.

## 🚀 Features

- **🤖 Multi-Model Support**: DeepSeek, Claude, OpenAI, Mercury
- **📊 Advanced Analysis**: Code quality, performance, security, framework-specific
- **🌐 Repository Analysis**: Clone and analyze entire GitHub repositories
- **📁 File Upload**: Support for multiple programming languages
- **🎯 Adaptive Evaluations**: Smart analysis based on code context
- **💫 Beautiful UI**: Modern gradient design with responsive layout

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Git (for repository analysis)

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API keys** (create a `.env` file):
   ```bash
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_claude_key_here
   DEEPSEEK_API_KEY=your_deepseek_key_here
   MERCURY_API_KEY=your_mercury_key_here
   ```

## 🎮 Usage

### Method 1: Using the run script (Recommended)
```bash
python run_streamlit.py
```

### Method 2: Direct Streamlit command
```bash
streamlit run code_analyzer/web/app.py
```

### Method 3: From the web directory
```bash
cd code_analyzer/web
streamlit run app.py
```

## 🎯 How to Use

1. **Choose your LLM model** from the sidebar
2. **Select analysis types** you want to perform
3. **Input your code** in one of three ways:
   - Paste code directly into the text area
   - Upload a code file
   - Provide a GitHub repository URL
4. **Click "Analyze Now"** and watch the magic happen!

## 📊 Analysis Types

- **Code Quality & Bugs**: Identifies potential issues and code smells
- **Performance Profiling**: Analyzes performance bottlenecks
- **Security Scan**: Detects security vulnerabilities
- **Framework-Specific**: Framework-aware analysis
- **Cloud Integration**: Cloud deployment recommendations
- **Container/K8s**: Containerization and orchestration analysis

## 🎨 UI Features

- **Responsive Design**: Works on desktop and mobile
- **Dark/Light Mode**: Automatic theme detection
- **Progress Indicators**: Real-time analysis progress
- **Tabbed Results**: Organized analysis output
- **Error Handling**: Graceful error messages

## 🔧 Configuration

### Sidebar Options
- **LLM Model**: Choose your preferred AI model
- **Analysis Types**: Select which analyses to run
- **Adaptive Evals**: Enable/disable adaptive evaluations

### Supported File Types
- Python (`.py`)
- JavaScript (`.js`)
- Java (`.java`)
- C++ (`.cpp`)
- C (`.c`)
- C# (`.cs`)
- PHP (`.php`)
- Ruby (`.rb`)
- Go (`.go`)
- Rust (`.rs`)
- Swift (`.swift`)
- Kotlin (`.kt`)

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Errors**: Verify your `.env` file has the correct API keys

3. **Repository Clone Failures**: Ensure the repository is public or you have proper access

4. **Port Already in Use**: Change the port in `run_streamlit.py` or kill existing processes

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify your API keys are correct
3. Ensure all dependencies are installed
4. Try running with a simple code snippet first

## 🔄 Migration from Flask

This Streamlit app replaces the previous Flask-based web interface with:
- ✅ Better UI/UX
- ✅ Easier deployment
- ✅ More interactive features
- ✅ Built-in state management
- ✅ Responsive design

## 📈 Performance

- **Fast Startup**: Optimized imports and lazy loading
- **Efficient Analysis**: Parallel processing where possible
- **Memory Management**: Automatic cleanup of temporary files
- **Caching**: Streamlit's built-in caching for repeated operations

## 🚀 Deployment

### Local Development
```bash
python run_streamlit.py
```

### Production Deployment
The app can be deployed to:
- Streamlit Cloud
- Heroku
- AWS/GCP/Azure
- Docker containers

## 📝 License

This project is part of the LLM Code Analyzer suite.

---

**Matrix theme added with custom CSS!**

**Ready to analyze some code? Let's go! 🚀** 

Matrix cyberpunk theme integrated with custom CSS. 