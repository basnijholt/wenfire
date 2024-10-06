# WenFire 🔥 Financial Independence Calculator 💸

Welcome to the WenFire Financial Independence Calculator GitHub repository! This web application helps users visualize their journey to financial independence and early retirement by calculating and plotting various financial metrics. The app is built using FastAPI and Bootstrap, and it's currently hosted on at https://wenfire.nijho.lt/.

There are many such calculators available, however, I couldn't find one with the salary growth assumptions that I wanted. I also just wanted to play FastAPI, htmx, and Vega-Lite. So I built this calculator to scratch my own itch, and I hope you find it useful too! 😄

![WenFire Screenshot](https://github.com/basnijholt/wenfire/assets/6897215/0d76a7f0-6c5f-4ead-967d-84be6fb5a5f5)

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
3. Install the required dependencies: `uv sync`
4. Run the FastAPI server: `uv run uvicorn wenfire.app:app --reload`
5. Open your browser and visit `http://localhost:8000/`

## Contributing 🤝

We welcome contributions to improve the WenFire Financial Independence Calculator! Feel free to submit an issue or pull request with your suggestions, bug reports, or feature requests. Happy coding! 🎉
