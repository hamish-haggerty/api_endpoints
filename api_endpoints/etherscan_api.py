# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/etherscan_api.ipynb.

# %% auto 0
__all__ = ['api_key', 'pepe_address', 'pepe_deployer', 'bybit_address', 'get_contract_creator', 'get_first_n_addresses',
           'get_last_n_transactions_for_erc20', 'get_creation_date']

# %% ../nbs/etherscan_api.ipynb 3
import requests
import json
import time

# %% ../nbs/etherscan_api.ipynb 5
api_key = 'DWNVAVM1GPZK3PUIKM79AQ2ZZS1JUPI417'  #my API key for etherscan

# %% ../nbs/etherscan_api.ipynb 6
#Several relevant addresses for debugging etc
pepe_address = '0x6982508145454Ce325dDbE47a25d4ec3d2311933' #Pepe address
pepe_deployer = '0xfbfEaF0DA0F2fdE5c66dF570133aE35f3eB58c9A' #Pepe deployer
bybit_address = '0xf89d7b9c864f589bbF53a82105107622B35EaA40'  #ByBit hot wallet associated with Pepe deployer....


# %% ../nbs/etherscan_api.ipynb 7
def get_contract_creator(contract_address:str, api_key:str)->str:
    
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={contract_address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"

    response = requests.get(url)
    data = json.loads(response.text)

    if data['status'] == '1':
        transactions = data['result']
        contract_creation_tx = transactions[0]  # the contract creation transaction is usually the first transaction
        return contract_creation_tx['from']  # the contract creator's address

    else:
        print("Error:", data['message'])
        return None


# %% ../nbs/etherscan_api.ipynb 14
# def get_total_eth_transacted(address, api_key):
#     url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=asc&apikey={api_key}"
#     response = requests.get(url)
#     transactions = json.loads(response.text)['result']
    
#     total_in = 0
#     total_out = 0
#     for txn in transactions:
#         value = int(txn['value']) / (10 ** 18)  # Convert from Wei to Ether
#         if txn['to'] == address.lower():
#             total_in += value
#         elif txn['from'] == address.lower():
#             total_out += value
    
#     return total_in, total_out

#Code to handle arbitrary number of transactions, which however seems to slow things down a lot, and we possibly do not
#even need it. So, we will stick to the above code for now.

# def get_total_eth_transacted(address, api_key):
#     startblock = 0
#     endblock = 99999999
#     total_in = 0
#     total_out = 0
    
#     while True:
#         url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock={startblock}&endblock={endblock}&sort=asc&apikey={api_key}"
#         response = requests.get(url)
#         transactions = json.loads(response.text)['result']
        
#         for txn in transactions:
#             value = int(txn['value']) / (10 ** 18)  # Convert from Wei to Ether
#             if txn['to'] == address.lower():
#                 total_in += value
#             elif txn['from'] == address.lower():
#                 total_out += value

#         # If less than 10000 transactions were returned, we've got them all
#         if len(transactions) < 10000:
#             break
#         else:
#             # Use the 'blockNumber' of the last transaction as 'startblock' for the next request
#             startblock = int(transactions[-1]['blockNumber']) + 1
            
#         # Sleep for a short period to respect API rate limits
#         time.sleep(0.2)
    
#     return total_in, total_out


# %% ../nbs/etherscan_api.ipynb 16
def get_first_n_addresses(contract_address:str, n:int, api_key:str)->dict:
    """Get the first n addresses holding a contract (e.g. erc20).
        Args:
            contract_address (str): The address of the contract.
            n (int): The number of first holders' addresses to retrieve.
            api_key (str): API key to authenticate the request.

        Returns:
            dict: A dictionary containing the first n addresses holding the contract. 
                  The keys are the addresses (which is the main thing we want). Values are tuples: (tx_hash,count)
                  where tx_hash is the hash of the transaction wherein the address received the contract
                  (mostly useful for debugging/logging purposes) and count records the order.
                  So e.g. count=0 ~ means the address is the first holder of the contract. We use the ~ symbol since e.g. mev
                  bots can be excluded from etherscan page.

        NOTE: mev bot transactions seem to not show up on etherscans page, so be careful with debugging.
        TODO: possibly need a way to handle the mev bot issue.

        Please see the documentation here: https://docs.etherscan.io/api-endpoints/accounts#get-a-list-of-erc20-token-transfer-events-by-address
    """
    holders_dict = {}
    count = 0
    page_num = 1
    
    while count < n:
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract_address}&startblock=0&endblock=99999999&page={page_num}&offset=100&sort=asc&apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if 'result' not in data or not data['result']:
            # No more data to process
            break
        
        for tx in data['result']:
            address = tx['to']
            if holders_dict.get(address,None)==None:  # Avoid duplicates
                holders_dict[address] = (tx['hash'],count)
                count += 1
                if count == n:
                    return holders_dict
        
        # Move to the next page of results
        page_num += 1

    return holders_dict


# %% ../nbs/etherscan_api.ipynb 24
def get_last_n_transactions_for_erc20(contract_address, n, api_key):
    """Fetch the last n transactions for an ERC-20 token.

    Args:
    - contract_address (str): The ERC-20 token's contract address.
    - n (int): The number of transactions to retrieve.
    - api_key (str): Your Etherscan API key.

    Returns:
    - list[dict]: A list of transaction dictionaries.
    """
    
    transactions_list = []
    page_num = 1
    
    while len(transactions_list) < n:
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract_address}&page={page_num}&offset=100&sort=desc&apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if 'result' not in data or not data['result']:
            # No more data to process
            break
        
        transactions_list.extend(data['result'])

        # If we've collected more than 'n' transactions, truncate the list
        if len(transactions_list) > n:
            transactions_list = transactions_list[:n]
            break
        
        # Move to the next page of results
        page_num += 1

    return transactions_list

if __name__ == "__main__":
# Example usage:
    contract_address = "0x02e7f808990638e9e67e1f00313037ede2362361" #kibshi
    n = 100

    transactions = get_last_n_transactions_for_erc20(contract_address, n, api_key)
    # for tx in transactions:
    #     print(tx)


# %% ../nbs/etherscan_api.ipynb 25
from typing import Optional, Union
from datetime import datetime

def get_creation_date(api_key: str, contract_address: str, network: Optional[str] = 'mainnet') -> Union[str, None]:
    """
    Fetch the creation date of an ERC20 contract using the Etherscan API.
    
    Parameters:
    - api_key (str): The API key for Etherscan.
    - contract_address (str): The Ethereum address of the contract.
    - network (Optional[str]): The Ethereum network ('mainnet', 'ropsten', etc.). Default is 'mainnet'.
    
    Returns:
    - str: The creation date in the format 'YYYY-MM-DD HH:MM:SS' in UTC if found.
    - None: If the contract has no transactions or the API request fails.
    """
    # Determine the base URL depending on the network
    base_url = 'https://api.etherscan.io/api?'
    if network != 'mainnet':
        base_url = f'https://{network}.etherscan.io/api?'

    # Define API parameters
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': contract_address,
        'startblock': 0,
        'endblock': 99999999,
        'sort': 'asc',
        'apikey': api_key
    }

    # Make API request
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = json.loads(response.text)
        if 'result' in data and len(data['result']) > 0:
            # The first transaction should be the contract creation transaction
            creation_transaction = data['result'][0]
            timestamp = int(creation_transaction['timeStamp'])
            creation_date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            return creation_date
        else:
            return None
    else:
        return None
