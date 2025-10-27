# KATH Developer Setup Guide

Welcome to the KATH development team! This guide will help you set up your development environment in less than 30 minutes.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (for running the full application)
- **Python 3.12+** (for backend development)
- **Node.js 20+** (for frontend development)
- **Git** (for version control)
- **VS Code** or your preferred IDE

## Quick Start (5 minutes)

If you just want to run KATH without modifying code:

```bash
# Clone the repository
git clone https://github.com/your-repo/kath.git
cd kath

# Run the application
./start-kath.sh  # Mac/Linux
# or
start-kath.bat   # Windows
```

The application will be available at http://localhost:5173

## Development Setup

### Backend Development Setup

1. **Navigate to backend directory:**
   ```bash
   cd app/back_end
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Mac/Linux
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_dev.txt  # For testing tools
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.development .env
   ```

5. **Download required data files:**

   **FASTA Reference (hg38):**
   ```bash
   mkdir -p src/workspace/fasta
   # Download from UCSC or your preferred source
   # Place hg38.fa in src/workspace/fasta/
   ```

   **REVEL Database:**
   ```bash
   mkdir -p src/workspace/revel
   # Follow instructions in app/back_end/README.md
   ```

6. **Start Redis (required for WebSocket):**
   ```bash
   redis-server
   ```

7. **Run the backend:**
   ```bash
   python run.py
   ```

   Backend will be available at http://localhost:8080

### Frontend Development Setup

1. **Navigate to frontend directory:**
   ```bash
   cd app/front_end
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.development .env
   ```

4. **Run the frontend:**
   ```bash
   npm run dev
   ```

   Frontend will be available at http://localhost:5173

### Running Tests

**Backend Tests:**
```bash
cd app/back_end
pytest
pytest --cov=src --cov-report=html  # With coverage report
```

**Frontend Tests:**
```bash
cd app/front_end
npm test
npm run lint  # Run ESLint
```

### Code Quality Checks

**Backend:**
```bash
# Format code with Black
black src/

# Sort imports
isort src/

# Type checking
mypy src/

# Linting
flake8 src/
```

**Frontend:**
```bash
# Format code
npm run format

# Lint
npm run lint
```

## Project Structure

```
kath-v0.2-alpha/
├── app/
│   ├── back_end/              # Python Flask backend
│   │   ├── src/               # Application source code
│   │   │   ├── routes/        # API endpoints
│   │   │   ├── tools/         # DNA analysis tools
│   │   │   ├── data/          # Data processing
│   │   │   ├── utils/         # Utilities
│   │   │   └── setup/         # App initialization
│   │   ├── tests/             # Backend tests
│   │   ├── run.py             # Application entry point
│   │   └── requirements.txt   # Python dependencies
│   │
│   ├── front_end/             # React TypeScript frontend
│   │   ├── src/
│   │   │   ├── app/           # App-level components
│   │   │   ├── features/      # Feature modules (editor)
│   │   │   ├── components/    # Shared components
│   │   │   ├── stores/        # Context providers
│   │   │   ├── hooks/         # Custom hooks
│   │   │   ├── lib/           # Library configs
│   │   │   └── types/         # TypeScript types
│   │   ├── package.json       # Node dependencies
│   │   └── vite.config.ts     # Vite configuration
│   │
│   ├── Dockerfile.final       # Production Docker image
│   └── run.sh                 # Container entry point
│
├── docs/                      # Documentation
├── start-kath.sh              # Mac/Linux launcher
├── start-kath.bat             # Windows launcher
├── HOW_TO_RUN.md             # User guide
└── REFACTORING_PLAN.md       # Development roadmap
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow the code style guidelines
- Write tests for new features
- Update documentation as needed

### 3. Run Tests

```bash
# Backend
cd app/back_end
pytest

# Frontend
cd app/front_end
npm test
npm run lint
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Common Development Tasks

### Adding a New API Endpoint

1. Create route handler in `app/back_end/src/routes/`
2. Register blueprint in `app/back_end/src/setup/router.py`
3. Add endpoint constant in `app/front_end/src/types/constants/endpoints.ts`
4. Update API documentation

### Adding a New DNA Analysis Tool

1. Create tool class in `app/back_end/src/tools/`
2. Implement tool logic (VCF generation, execution, parsing)
3. Add route in `app/back_end/src/routes/workspace_apply_route.py`
4. Add frontend button in toolbar
5. Test with sample data

### Adding a Frontend Component

1. Create component in appropriate directory:
   - Shared: `app/front_end/src/components/`
   - Feature-specific: `app/front_end/src/features/editor/components/`
2. Define TypeScript interfaces
3. Implement component with MUI styling
4. Export from index file

### Modifying Database Schema (Future)

Once we migrate to SQLite (Phase 2):
1. Create Alembic migration: `alembic revision -m "description"`
2. Implement `upgrade()` and `downgrade()` functions
3. Test migration on development database
4. Run migration: `alembic upgrade head`

## Debugging

### Backend Debugging

**Using VS Code:**
1. Install Python extension
2. Create `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: Flask",
         "type": "python",
         "request": "launch",
         "module": "flask",
         "env": {
           "FLASK_APP": "run.py",
           "FLASK_ENV": "development"
         },
         "args": ["run", "--no-debugger"],
         "jinja": true
       }
     ]
   }
   ```
3. Set breakpoints and press F5

**Using print debugging:**
```python
from src.utils.logger import logger

logger.info(f"Processing variant: {variant}")
logger.error(f"Error occurred: {str(e)}")
```

### Frontend Debugging

**Chrome DevTools:**
1. Open http://localhost:5173
2. Press F12 to open DevTools
3. Use Console, Network, and React DevTools tabs

**VS Code:**
1. Install Debugger for Chrome extension
2. Set breakpoints in TypeScript files
3. Press F5 to start debugging

## Environment Variables

### Backend (.env)

```env
# Flask Configuration
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=8080

# CORS Origins
ORIGINS=http://localhost:5173

# Redis
REDIS_URL=redis://localhost:6379/0

# SpliceAI
CUDA=False
CUDA_BATCH_SIZE=32

# Processing Limits
MAX_ENTRIES=999999999
```

### Frontend (.env)

```env
# API Configuration
VITE_API_URL=http://localhost:8080/api/v1
VITE_SOCKET_URL=http://localhost:8080

# Build Configuration
PORT=5173
```

## Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'src'`
**Solution:** Ensure you're in the `app/back_end` directory and virtual environment is activated.

**Problem:** `redis.exceptions.ConnectionError`
**Solution:** Start Redis server: `redis-server`

**Problem:** SpliceAI fails with CUDA error
**Solution:** Set `CUDA=False` in `.env` or install CUDA toolkit.

### Frontend Issues

**Problem:** `Cannot find module '@/...'`
**Solution:** Restart the dev server after installing dependencies.

**Problem:** API requests failing with CORS error
**Solution:** Check `ORIGINS` in backend `.env` matches frontend URL.

**Problem:** WebSocket not connecting
**Solution:** Ensure backend is running and Socket.IO port (8080) is accessible.

## Database Development (Coming in Phase 2)

Once we implement SQLite database:

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Database CLI
```bash
# Open SQLite shell
sqlite3 data/kath.db

# Run queries
SELECT COUNT(*) FROM variants;
```

## Performance Profiling

### Backend Profiling

```python
from cProfile import Profile
from pstats import Stats

profiler = Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(10)
```

### Frontend Profiling

Use React DevTools Profiler:
1. Open React DevTools
2. Go to Profiler tab
3. Click Record
4. Perform actions
5. Stop and analyze flamegraph

## CI/CD Pipeline (Coming Soon)

Our GitHub Actions workflow will:
- Run all tests on pull requests
- Check code formatting
- Build Docker images
- Deploy to staging/production

## Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [Material-UI Documentation](https://mui.com/)
- [Socket.IO Documentation](https://socket.io/docs/)

### KATH-Specific Docs
- [API Reference](./api/API_REFERENCE.md)
- [Architecture Overview](./architecture/ARCHITECTURE.md)
- [Refactoring Plan](../REFACTORING_PLAN.md)

### External Tools
- [SpliceAI GitHub](https://github.com/Illumina/SpliceAI)
- [CADD Website](https://cadd.gs.washington.edu/)
- [REVEL Downloads](https://sites.google.com/site/revelgenomics/)

## Getting Help

- **Issues:** Check existing issues or create a new one on GitHub
- **Questions:** Ask in team Slack channel or daily standup
- **Documentation:** Check `/docs` directory for detailed guides

## Contributing Guidelines

1. **Code Style:**
   - Backend: Follow PEP 8, use Black formatter
   - Frontend: Follow Airbnb style guide, use Prettier

2. **Testing:**
   - Write tests for all new features
   - Maintain test coverage above 70%

3. **Documentation:**
   - Update API docs when adding endpoints
   - Add JSDoc comments for complex functions
   - Update user guide for user-facing features

4. **Pull Requests:**
   - Keep PRs small and focused
   - Write clear descriptions
   - Request review from at least one team member
   - Ensure CI passes before merging

## Next Steps

Now that your environment is set up:

1.  Run the application locally
2.  Explore the codebase
3.  Read the [Architecture Overview](./architecture/ARCHITECTURE.md)
4.  Pick a task from the [Refactoring Plan](../REFACTORING_PLAN.md)
5.  Make your first contribution!

Welcome to the team! 
