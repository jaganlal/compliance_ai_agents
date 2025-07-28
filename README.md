# CPG Compliance AI Agents Project
If a CPG has a contract in a particular retail store #8 (walmart) that their aisle # 5 will be 100% rented by the CPG company and only their products must be stocked and aisle #27 will be 50% rented and stock their products

## Project Overview
This project implements an autonomous AI agent system for monitoring CPG product compliance in retail stores using Azure ecosystem technologies. The system processes daily store images, validates product placement against planograms, and generates compliance reports.

## Architecture
- CrewAI: Orchestration and workflow management
- LangChain: Contract intelligence and RAG operations
- Autogen: Multi-agent conversations and image analysis
- LangGraph: Planogram validation workflows
- Azure Services: Storage, messaging, and infrastructure (mocked locally)

## Quick Start
### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for dashboard)
- VS Code (recommended)

### Setup

```
# Clone and setup
git clone <repository-url>
cd compliance_ai_agents

# Environment setup
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d

# Install dependencies
pip install -r requirements.txt
cd dashboard && npm install && cd ..

# Run the system
python main.py
```

### Complete Setup Instructions

#### 1. Download and Setup
```
# Create project directory
mkdir compliance_ai_agents
cd compliance_ai_agents

# Copy all the files from the playground above into respective directories
# Then run setup
python setup.py
```

#### 2. Quick Start Commands
```
# Activate environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Generate mock data
python cli.py generate-mock-data

# Run single compliance check
python cli.py check-compliance --store-id STORE_0001

# Start continuous monitoring
python cli.py start-monitoring

# Check system status
python cli.py status
```

#### 3. Docker Setup (Alternative)
```
# Build and run with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Access Points
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- CLI: python cli.py --help

### Project Structure

```
compliance_ai_agents/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.dev.yml
├── Dockerfile
├── main.py                     # Main application entry point
├── cli.py                      # Command-line interface
├── config/
│   ├── __init__.py
│   ├── settings.py             # Configuration management
│   ├── azure_config.py         # Azure service configurations
│   └── logging_config.py       # Logging setup
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Base agent class
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── crew_orchestrator.py    # CrewAI orchestration
│   │   └── workflow_manager.py     # Workflow coordination
│   ├── contract_intelligence/
│   │   ├── __init__.py
│   │   ├── langchain_agent.py      # LangChain contract agent
│   │   ├── rag_system.py           # RAG implementation
│   │   └── contract_parser.py      # Contract parsing logic
│   ├── image_analysis/
│   │   ├── __init__.py
│   │   ├── autogen_analyzer.py     # Autogen image analysis
│   │   ├── vision_processor.py     # Computer vision processing
│   │   └── compliance_detector.py  # Compliance detection
│   ├── planogram_validation/
│   │   ├── __init__.py
│   │   ├── langgraph_validator.py  # LangGraph validation
│   │   ├── planogram_matcher.py    # Planogram matching
│   │   └── layout_analyzer.py      # Layout analysis
│   └── reporting/
│       ├── __init__.py
│       ├── report_generator.py     # Report generation
│       ├── alert_manager.py        # Alert management
│       └── compliance_calculator.py # Compliance metrics
├── services/
│   ├── __init__.py
│   ├── azure_services/
│   │   ├── __init__.py
│   │   ├── blob_storage.py         # Azure Blob Storage mock
│   │   ├── service_bus.py          # Azure Service Bus mock
│   │   ├── cognitive_services.py   # Azure Cognitive Services mock
│   │   └── cosmos_db.py            # Azure Cosmos DB mock
│   ├── communication/
│   │   ├── __init__.py
│   │   ├── a2a_protocol.py         # Agent-to-Agent communication
│   │   ├── message_broker.py       # Message brokering
│   │   └── event_dispatcher.py     # Event dispatching
│   └── data/
│       ├── __init__.py
│       ├── data_manager.py         # Data management
│       ├── cache_manager.py        # Caching system
│       └── storage_manager.py      # Storage operations
├── memory/
│   ├── __init__.py
│   ├── episodic_memory.py          # Episodic memory implementation
│   ├── semantic_memory.py          # Semantic memory implementation
│   ├── working_memory.py           # Working memory implementation
│   └── memory_manager.py           # Memory coordination
├── models/
│   ├── __init__.py
│   ├── compliance_models.py        # Compliance data models
│   ├── contract_models.py          # Contract data models
│   ├── image_models.py             # Image data models
│   └── report_models.py            # Report data models
├── utils/
│   ├── __init__.py
│   ├── image_utils.py              # Image processing utilities
│   ├── validation_utils.py         # Validation utilities
│   ├── date_utils.py               # Date/time utilities
│   └── mock_data_generator.py      # Mock data generation
├── tests/
│   ├── __init__.py
│   ├── test_agents/
│   ├── test_services/
│   ├── test_memory/
│   └── test_utils/
├── dashboard/                      # Web dashboard
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.js
│   └── public/
├── data/                          # Local data storage
│   ├── contracts/                 # Contract documents
│   ├── planograms/               # Planogram files
│   ├── images/                   # Store images
│   ├── reports/                  # Generated reports
│   └── cache/                    # Cache storage
└── docs/                         # Documentation
    ├── architecture.md
    ├── api_reference.md
    ├── deployment_guide.md
    └── user_guide.md
```