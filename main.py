import datetime
import requests
import json
import time
import os.path
import re
from telegram.ext import Updater, CommandHandler


# Update the following variables with your own Etherscan and BscScan API keys and Telegram bot token
ETHERSCAN_API_KEY = 'CKNNT8S3WW8G5IZ3KK1VEHVSAPMRHMJQ4B'
BSCSCAN_API_KEY = 'SZSR36ZQ18HFBBJVW43DCZF22XKUW5SU2N'
TELEGRAM_BOT_TOKEN = '5343231561:AAGB0nKpggD61U7t83sNgW_a0baKCQk2Deo'
TELEGRAM_CHAT_IDs = ['556907227']
TELEGRAM_CHAT_ID_ADMIN = '556907227'


# Define some helper functions
def get_wallet_transactions(wallet_address, blockchain):
    if blockchain == 'eth':
        url = f'https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={ETHERSCAN_API_KEY}'
    elif blockchain == 'bnb':
        url = f'https://api.bscscan.com/api?module=account&action=txlist&address={wallet_address}&sort=desc&apikey={BSCSCAN_API_KEY}'
    else:
        raise ValueError('Invalid blockchain specified')

    response = requests.get(url)
    data = json.loads(response.text)

    result = data.get('result', [])
    if not isinstance(result, list):
        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error fetching transactions for {wallet_address} on {blockchain.upper()} blockchain: {data}")
        return []

    return result


def send_telegram_notification(message, value, p_or_m, usd_value, tx_hash, blockchain):
    if blockchain == 'eth':
        etherscan_link = f'<a href="https://etherscan.io/tx/{tx_hash}">Etherscan</a>'
    elif blockchain == 'bnb':
        etherscan_link = f'<a href="https://bscscan.com/tx/{tx_hash}">BscScan</a>'
    else:
        raise ValueError('Invalid blockchain specified')
    for i in range(len(TELEGRAM_CHAT_IDs)):

        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        payload = {'chat_id': f'{TELEGRAM_CHAT_IDs[i]}',
                   'text': f'{message}: {etherscan_link}\nValue: {p_or_m}{value:.6f} {blockchain.upper()} (${usd_value:.2f})',
                   'parse_mode': 'HTML'}
        response = requests.post(url, data=payload)
        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Telegram notification sent with message: {message}, value: {p_or_m}{value} {blockchain.upper()} (${usd_value:.2f})")
    return response


def monitor_wallets():
    watched_wallets = set()
    file_path = "watched_wallets.txt"
    if not os.path.exists(file_path):
        open(file_path, 'w').close()

    latest_tx_hashes = {}
    latest_tx_hashes_path = "latest_tx_hashes.json"
    if os.path.exists(latest_tx_hashes_path):
        with open(latest_tx_hashes_path, "r") as f:
            latest_tx_hashes = json.load(f)

    last_run_time = 0
    last_run_time_path = "last_run_time.txt"
    if os.path.exists(last_run_time_path):
        with open(last_run_time_path, "r") as f:
            last_run_time = int(f.read())

    while True:
        try:
            # Fetch current ETH and BNB prices in USD from CoinGecko API
            eth_usd_price_url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum%2Cbinancecoin&vs_currencies=usd'
            response = requests.get(eth_usd_price_url)
            data = json.loads(response.text)
            eth_usd_price = data['ethereum']['usd']
            bnb_usd_price = data['binancecoin']['usd']

            # Read from file
            with open(file_path, 'r') as f:
                watched_wallets = set(f.read().splitlines())

            for wallet in watched_wallets:
                blockchain, wallet_address, name_of_wallet = wallet.split(':')
                transactions = get_wallet_transactions(wallet_address, blockchain)
                for tx in transactions:
                    tx_hash = tx['hash']
                    tx_time = int(tx['timeStamp'])

                    if tx_hash not in latest_tx_hashes and tx_time > last_run_time:
                        tm = tx['timeStamp']
                        value = float(tx['value']) / 10 ** 18  # Convert from wei to ETH or BNB
                        date_time = datetime.datetime.fromtimestamp(int(tm)+7200)
                        date_time_str = date_time.strftime('%Y-%m-%d %H:%M:%S')
                        if tx['to'].lower() == wallet_address.lower() and value > 0.001:

                            usd_value = value * (
                                eth_usd_price if blockchain == 'eth' else bnb_usd_price)  # Calculate value in USD

                            message = f'🚨 <i>BUY transaction detected on:</i>\n'
                            message += f'  - <b>Name of the wallet:</b> {name_of_wallet}\n'
                            message += f'  - <b>Time:</b> {date_time_str}\n'
                            try:
                                contract_address = tx['from']
                                r = requests.get((f'https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey={ETHERSCAN_API_KEY}'))
                                contract_name = r.json()['result'][0]['ContractName']
                                if contract_name != '':
                                    message += f'  - from: <b>{contract_name}</b>\n'
                            except:
                                pass
                            p_or_m = "-"
                            send_telegram_notification(message, value, p_or_m, usd_value, tx['hash'], blockchain)
                        elif tx['from'].lower() == wallet_address.lower() and value > 0.001:
                            usd_value = value * (
                                eth_usd_price if blockchain == 'eth' else bnb_usd_price)  # Calculate value in USD
                            message = f'🚨 <i>SELL transaction detected on:</i>\n'
                            message += f'  - Name of the wallet: <b>{name_of_wallet}</b>\n'
                            message += f'  - <b>Time:</b> {date_time_str}\n'
                            try:
                                contract_address = tx['to']
                                r = requests.get((f'https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey={ETHERSCAN_API_KEY}'))
                                contract_name = r.json()['result'][0]['ContractName']
                                if contract_name != '':
                                    message += f'  - from: <b>{contract_name}</b>\n'
                            except:
                                print('ni')
                            p_or_m = "+"
                            send_telegram_notification(message, value, p_or_m, usd_value, tx['hash'], blockchain)

                        latest_tx_hashes[tx_hash] = int(tx['blockNumber'])

            # Save latest_tx_hashes to file
            with open(latest_tx_hashes_path, "w") as f:
                json.dump(latest_tx_hashes, f)

            # Update last_run_time
            last_run_time = int(time.time())
            with open(last_run_time_path, "w") as f:
                f.write(str(last_run_time))

            # Sleep for 15 minute
            time.sleep(900)
        except Exception as e:
            print(f'An error occurred: {e}')
            # Sleep for 10 seconds before trying again
            time.sleep(10)


def add_wallet(wallet_address, blockchain, name_of_wallet):
    file_path = "watched_wallets.txt"
    with open(file_path, 'a') as f:
        f.write(f'{blockchain}:{wallet_address}:{name_of_wallet}\n')


def remove_wallet(wallet_address, blockchain, name_of_wallet):
    file_path = "watched_wallets.txt"
    temp_file_path = "temp.txt"
    with open(file_path, 'r') as f, open(temp_file_path, 'w') as temp_f:
        for line in f:
            if line.strip() != f'{blockchain}:{wallet_address}:{name_of_wallet}':
                temp_f.write(line)
    os.replace(temp_file_path, file_path)


# Define the command handlers for the Telegram bot
def start(update, context):
    message = """
    👋 *Welcome to the Ethereum and Binance Wallet Monitoring Bot!*

    To add a new wallet to monitor, use the command:
    /add <blockchain> <wallet_address> <name_of_wallet>

    Example: /add ETH 0x123456789abcdef MyETHWallet

    To stop monitoring a wallet, use the command:
    /remove <blockchain> <wallet_address> <name_of_wallet>

    Example: /remove ETH 0x123456789abcdef MyETHWallet

    To list all wallets being monitored for a specific blockchain, use the command:
    /list <blockchain>

    Example: /list ETH

    To list all wallets being monitored for all blockchains, use the command:
    /list

    """


    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='Markdown')


def add(update, context):
    user_id = update.effective_user.id
    if user_id != int(TELEGRAM_CHAT_ID_ADMIN):
        message = "You do not have permission to run this command."
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='Markdown')
        return
    if len(context.args) < 2:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="Please provide a blockchain and wallet address to add and name of the wallet  Example: /add ETH 0x123456789abcdef MyETHWallet")
        return

    blockchain = context.args[0].lower()
    wallet_address = context.args[1]
    name_of_wallet = context.args[2]
    print(context)
    print(blockchain, wallet_address, wallet_address)
    # Check if the wallet address is in the correct format for the specified blockchain
    if blockchain == 'eth':
        if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
            context.bot.send_message(chat_id=update.message.chat_id,
                                     text=f"{wallet_address} is not a valid Ethereum wallet address.")
            return
    elif blockchain == 'bnb':
        if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
            context.bot.send_message(chat_id=update.message.chat_id,
                                     text=f"{wallet_address} is not a valid Binance Smart Chain wallet address.")
            return
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Invalid blockchain specified: {blockchain}")
        return

    add_wallet(wallet_address, blockchain, name_of_wallet)
    message = f'Added {wallet_address} to the list of watched {blockchain.upper()} wallets and name of wallet {name_of_wallet}.'
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


def remove(update, context):
    user_id = update.effective_user.id
    if user_id != int(TELEGRAM_CHAT_ID_ADMIN):
        message = "You do not have permission to run this command."
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='Markdown')
        return
    if len(context.args) < 2:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="Please provide a blockchain and wallet address to remove.\nExample: /remove ETH 0x123456789abcdef MyETHWallet")
        return
    blockchain = context.args[0].lower()
    wallet_address = context.args[1]
    name_of_wallet = context.args[2]
    remove_wallet(wallet_address, blockchain, name_of_wallet)
    message = f'Removed {wallet_address} from the list of watched {blockchain.upper()} wallets.'
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


def list_wallets(update, context):

    with open("watched_wallets.txt", "r") as f:
        wallets = [line.strip() for line in f.readlines()]
    if wallets:
        eth_wallets = []
        bnb_wallets = []
        print(eth_wallets)
        for wallet in wallets:
            blockchain, wallet_address, name_of_wallet = wallet.split(':')
            if blockchain == 'eth':
                eth_wallets.append(wallet_address + "  " + name_of_wallet)
            elif blockchain == 'bnb':
                bnb_wallets.append(wallet_address + "  " + name_of_wallet)

        message = "The following wallets are currently being monitored\n"
        message += "\n"
        if eth_wallets:
            message += "*Ethereum Wallets*:\n"
            for i, wallet in enumerate(eth_wallets):
                message += f"{i + 1}. {wallet}.{name_of_wallet}\n"
            message += "\n"
        if bnb_wallets:
            message += "*Binance Coin Wallets*:\n"
            for i, wallet in enumerate(bnb_wallets):
                message += f"{i + 1}. {wallet}.{name_of_wallet}\n"
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='Markdown')
    else:
        message = "There are no wallets currently being monitored."
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='Markdown')


def addchat(update, context):
    user_id = update.effective_user.id
    if user_id != int(TELEGRAM_CHAT_ID_ADMIN):
        message = "You do not have permission to run this command."
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='Markdown')
        return

    message = f'chat added to the list {update.message.chat_id}'
    TELEGRAM_CHAT_IDs.append(update.message.chat_id)
    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='Markdown')


def removechat(update, context):
    user_id = update.effective_user.id
    if user_id != int(TELEGRAM_CHAT_ID_ADMIN):
        message = "You do not have permission to run this command."
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='Markdown')
        return
    chat_id = update.message.chat_id
    if chat_id in TELEGRAM_CHAT_IDs:
        TELEGRAM_CHAT_IDs.remove(chat_id)
        message = f'Chat {chat_id} removed from the list.'
    else:
        message = f'Chat {chat_id} not found in the list.'
    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='Markdown')


updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Define the command handlers
start_handler = CommandHandler('start', start)
add_handler = CommandHandler('add', add)
remove_handler = CommandHandler('remove', remove)
list_handler = CommandHandler('list', list_wallets)
addchat_handler = CommandHandler('addchat', addchat)
removechat_handler = CommandHandler('removechat', removechat)

# Add the command handlers to the dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(add_handler)
dispatcher.add_handler(remove_handler)
dispatcher.add_handler(list_handler)
dispatcher.add_handler(addchat_handler)
dispatcher.add_handler(removechat_handler)

updater.start_polling()
print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Telegram bot started.")

print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitoring wallets...")
monitor_wallets()
