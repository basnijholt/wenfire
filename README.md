# WenFire 🔥 Financial Independence Calculator 💸

Welcome to the WenFire Financial Independence Calculator GitHub repository! This web application helps users visualize their journey to financial independence and early retirement by calculating and plotting various financial metrics. The app is built using FastAPI and Bootstrap, and it's currently hosted on Azure at https://wenfire.azurewebsites.net/.

![WenFire Screenshot](./screenshot.png)

## Features 🌟

- Responsive and mobile-friendly design using Bootstrap 📱
- Visualizations using Vega-Lite 📊
- Customizable assumptions for investment growth, inflation, and more ⚙️
- Calculates key metrics like retirement age, net worth, and safe withdrawal amounts 💰

## Assumptions and Limitations 🔍

This calculator is a useful tool for estimating your journey to financial independence, but it's important to remember the following assumptions and limitations:

1. 💹 **Investment Growth**: Assumes a fixed annual growth rate for your investments. Actual returns may vary due to market conditions.
2. 💰 **Inflation**: Assumes a constant inflation rate throughout your journey. In reality, inflation rates can vary over time.
3. 📈 **Salary Increases**: Assumes a constant annual salary increase. Changes in your career or job market can impact your income growth.
4. 🛍️ **Spending**: Assumes constant monthly spending, adjusted for inflation. In real life, your expenses might change due to lifestyle changes or unexpected events.
5. 💵 **Safe Withdrawal Rate**: Uses the popular 4% rule, which assumes that you can withdraw 4% of your portfolio annually without running out of money in retirement. This rule is based on historical data, and future market conditions might require adjustments to your withdrawal rate.

Always be prepared to review and adjust your financial plans based on your personal situation and the ever-changing world around us. Stay curious, keep learning, and always be prepared to adapt! 😃

## How to Run Locally 🚀

1. Clone this repository: `git clone https://github.com/basnijholt/wenfire.git`
2. Navigate to the project folder: `cd wenfire`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Run the FastAPI server: `uvicorn main:app --reload`
5. Open your browser and visit `http://localhost:8000/`

### Run locally with Azure Functions on MacOS ARM 🍎

Install the Azure Functions CLI tool

```bash
x86brew tap azure/functions
x86brew install azure-functions-core-tools@4
```

Create a x86 environment (because of ARM incompatibility)

```bash
ENV_NAME="x86python39"
CONDA_SUBDIR=osx-64 micromamba create -n $ENV_NAME python=3.9
micromamba activate $ENV_NAME
pip install -r requirements.txt
```

Start the function with

```bash
/usr/local/bin/func start
```

## Contributing 🤝

We welcome contributions to improve the WenFire Financial Independence Calculator! Feel free to submit an issue or pull request with your suggestions, bug reports, or feature requests. Happy coding! 🎉
