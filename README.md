# TONPAY - Telegram Crypto Wallet on the TON Blockchain

A powerful, multi-user crypto wallet built with Python, designed to operate
seamlessly within Telegram.
With initial support for the TON blockchain, TONPAY offers a convenient way
for users to manage crypto assets directly from Telegram.
Future updates may bring support for Ethereum (ETH) and Binance
Coin (BNB).

![alt text](https://github.com/hadif1999/tonpay/blob/master/assests/main.png?raw=true)
![alt text](https://github.com/hadif1999/tonpay/blob/master/assests/wallets.png?raw=true)
![alt text](https://github.com/hadif1999/tonpay/blob/master/assests/wallet.png?raw=true)

## Description

TONPAY is a Telegram-based crypto wallet bot developed to provide users a
secure, easy-to-use solution for managing their TON assets directly within Telegram.
The bot leverages Python, SQLModel as its ORM, and the TON blockchain to enable transactions,
storage, and management of wallets for multiple users With a focus on simplicity and accessibility.

## Features

- **User-Friendly Interface** - Interact with the bot within Telegram for seamless crypto management.
- **Multi-User Support** - Capable of handling multiple users concurrently.
- **Secure Wallet Management** - Each user can create and manage their own wallet.
- **TON Blockchain Integration** - Currently supports TON with plans to support ETH and BNB.
- **Scalable ORM** - Built with SQLModel to efficiently manage user data and wallet information.
- **Fully Asynchronous** - fully asynchronous code for almost all interactions even connecting to database.  

## Dependencies

- **[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot):** Enables integration with Telegram,
allowing the bot to handle user commands and actions.
- **[TonTools / ton](https://github.com/psylopunk/pytonlib.git):** Provides essential tools and libraries for interacting with the TON blockchain.
- **[wolfcrypt](https://github.com/wolfssl/wolfcrypt-py):** used for Authentication.

For a complete list of dependencies, see the requirements.txt file.
<br>
make sure above packages installed properly as sometimes there are problems with their installation.

## Installation
To set up TONPAY on your local environment:
1. **Clone the repository:**
``` bash
git clone https://github.com/hadif1999/tonpay.git
cd tonpay
```
2. **Set up a virtual environment (optional but recommended):**
``` bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```
3. **Install dependencies:**
``` bash
pip install -r requirements.txt
```
4. **setup config.json file for your own needs** 
5. **start a sql database server (postgres recommended)**
6. **Set up environment variables (e.g., Telegram Bot Token, database URI) in a .env file:**
``` bash 
TELEGRAM_TOKEN=your_telegram_token
DB_URI=<DB_USER>:<DB_SECRET>@<DB_HOST>/<DB_NAME>
```
7. **Run the bot:**
   
``` bash
python3 __main__.py # or just run "python3 ."
```

## Configuration File

TONPAY includes a configuration file, config.json,
which allows users to customize various aspects of
the wallet bot to suit their needs. In this file, users can:

- **Set up blockchain parameters** - Define the blockchain networks supported (currently TON, with plans for ETH and BNB).
- **Adjust authentication settings** - Modify the template used for the wallet authentication key (see details below).
- **Define scheduler options** - Customize the intervals for scheduled tasks, such as regular balance updates.
- **Set logging preferences** - Configure log levels, formats, and outputs for easier debugging and monitoring.

## Authentication Method

TONPAY uses a symmetric authentication mechanism to secure
user wallets. Each wallet is protected by a unique key
that is generated based on specific user data, the date the wallet
was created, and other details.
This symmetric key provides a semi-reliable method for user
authentication within the bot.
> [!WARNING]
> **this Authentication method might not be reliable enough for production, this only used for development. use with your own risk**

### Key Template Customization

The key generation template used in TONPAY is configurable in the config.json file.
By modifying this template, users can adjust the elements used to create
the authentication key, such as including additional user-specific information or
modifying the date format. This customization option allows developers to
enhance security or adjust the key structure to fit specific operational requirements.

## Future Plans

**Multi-blockchain Support** - Adding support for Ethereum (ETH) and Binance Coin (BNB).




