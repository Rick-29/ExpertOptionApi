# ExpertOption API

## Overview

This project provides an unofficial API for Expert Option, a popular binary options trading broker. The API allows you to programmatically interact with the platform, enabling automated trading, data analysis, and more.

**Project Link:** [ExpertOptionApi on GitHub](https://github.com/theshadow76/ExpertOptionApi)

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Contribution](#contribution)
- [License](#license)

## Installation

To get started with this API, you'll need to clone the repository and install the required packages.

```bash
git clone https://github.com/theshadow76/ExpertOptionApi.git
cd ExpertOptionApi
pip install -r requirements.txt
```
or 
```bash
pip install ExpertOptionAPI
```

## Usage

Here's how to initialize the API and make a simple request:

```python
from expert_option_api import ExpertOptionApi

# Initialize the API
api = ExpertOptionApi(username='your_username', password='your_password')

# Perform operations
api.buy('EURUSD', 1, 'call', 1)
```

## Examples

Examples of how to use this API for various tasks are available in the `examples` directory of the repository.

## Contribution

Contributions are welcome! Feel free to submit a pull request or raise an issue.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## PyPi link
[ExpertOptionAPI](https://pypi.org/project/ExpertOptionAPI/)
