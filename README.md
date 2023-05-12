
# Transaction_Tracking

## Description

This script allows you to track wallets and get notified in Telegram when a transaction occurs. It uses the following libraries: datetime, requests, json, time, os.path, re, and web3.

The Telegram bot has the following commands:

-   `/list` - shows all wallets
-   `/list eth` - shows wallets only in the Ethereum network
-   `/list bsc` - shows wallets only in the Binance Smart Chain network
-   `/add <adress> <personal_name>` - add a wallet
-   `/remove <adress> <personal_name>` - remove a wallet
-   `/start` - shows the description of the bot

The script uses the APIs from Ethscan and Bscscan to retrieve the wallet information and monitor transactions.

## Requirements

-   Python 3.x
-   `requests` 
-   `json` 
-   `time` 
-   `web3` 
-  `datetime` 

## Installation

1.  Clone the repository or download the script.
2.  Install the required libraries: `pip install -r requirements.txt`.
3.  Open the script and fill in the required variables.
4.  Run the script: `python script.py`.

## Configuration

Before running the script, you need to configure the following variables:

-   `TELEGRAM_BOT_TOKEN` - Telegram Bot API token
-   `TELEGRAM_CHAT_ID` - Telegram Chat ID
-   `ETHERSCAN_API_KEY` - Ethscan API key
-   `BSCSCAN_API_KEY` - Bscscan API key

To obtain a Telegram Bot API token, follow the instructions provided by the BotFather.

To obtain a Chat ID, you can use the Telegram API or simply send a message to your bot and retrieve the Chat ID from the message.

To obtain an Ethscan API key, register at [https://etherscan.io/apis](https://etherscan.io/apis) and follow the instructions.

To obtain a Bscscan API key, register at [https://bscscan.com/apis](https://bscscan.com/apis) and follow the instructions.

## Usage

1.  Run the script: `python script.py`.
2.  Send commands to the Telegram bot to manage the wallets and receive notifications.

##  Contributing

If you want to contribute to the project, you can fork the repository, make your changes, and submit a pull request. Please make sure to follow the coding style used in the project and include tests for your changes.
