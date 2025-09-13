# Financial Optimizer

A comprehensive financial analysis and optimization tool for businesses and individuals.

## Main Application

**`simple_app.py`** - The main and only application file. This is your single source of truth for the Financial Optimizer.

### Features
- **Multi-Mode Support**: Business, Personal, Charity, and Non-Profit modes
- **Investment Management**: Complete investment analysis with savings calculations
- **Dynamic Tabs**: Tab configuration changes based on selected mode
- **Real-time Calculations**: Automated savings calculations based on business data
- **Investment Types**: Capital Equipment, Process Improvement, People Training, Maintenance, and more
- **Personal Mode**: Complete with Financial Dashboard, Investment Management, Market Dashboard, Analysis, Data Input, and Account Management tabs
- **Subscription Management**: Tiered subscription system with international compliance

### Running the Application
```bash
python simple_app.py
```

The application will start on http://127.0.0.1:8050

## Key Architecture Files
- `modules/personal_mode/` - Complete Personal Mode implementation with 6 tabs and enhanced features
- `modules/market_dashboard/` - Market Dashboard functionality
- `investment_forms.py` - Modal forms for investment data input
- `requirements.txt` - Python dependencies
- Various specification documents in markdown format for reference

## Current Status
- **Personal Mode**: Complete implementation with all 6 tabs functional
- **Business Mode**: Financial Dashboard, Data Input, Investment Management, Financial Statements, Reports
- **Market Dashboard**: Real-time market monitoring and analysis
- **Subscription System**: Multi-tiered with international compliance (UK FCA, EU GDPR/MiFID II, US SEC)

## Next Actions
- **Portfolio Performance Chart**: Implement interactive portfolio performance chart with real-time data visualization and time period selection (1M, 6M, 1Y, 5Y) in the Financial Dashboard tab

## Development Notes
- This is the single source of truth for the Financial Optimizer application
- Personal Mode includes comprehensive UI layouts with subscription-based feature gating
- The application supports dynamic business data input and automated savings calculations
- Investment management tab includes comprehensive forms for different investment types
- Complete specification documents available for all major features

## Documentation
- `PERSONAL_MODE_COMPREHENSIVE_FEATURE_SPECIFICATION.md` - Complete feature documentation
- `SUBSCRIPTION_MANAGEMENT_AND_COMPLIANCE_SPECIFICATION.md` - Goal-based subscription framework with international compliance
- `PERSONAL_MODE_TAB_INPUTS_OUTPUTS_SPECIFICATION.md` - Complete I/O specifications for all Personal Mode features
- `USER_WORKFLOW_IMPLEMENTATION_PLAN.md` - User workflow-based development strategy and implementation plan
- `SPECIFICATION_CHANGE_MANAGEMENT_DOCUMENT.md` - Change tracking and update requirements for goal-based subscription migration
- Various other specification documents for detailed technical reference
