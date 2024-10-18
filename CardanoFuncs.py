import bech32
import requests
from config import cardanoAddress, cardanoscanHeader, coinmarketcapHeader, blockfrostHeader, blockfrostAPI, faucetFundedAddr
from pycardano import *
from blockfrost import ApiUrls
from math import ceil

def hex_to_bech32(hex_address, hrp='addr'):
    # Convert hexadecimal string to a list of integers
    data = [int(hex_address[i:i+2], 16) for i in range(0, len(hex_address), 2)]
    # Convert the list of integers to Bech32 format
    converted_data = bech32.convertbits(data, 8, 5, True)
    return bech32.bech32_encode(hrp, converted_data)

def bech32_to_hex(bech32_address):
    hrp, data = bech32.bech32_decode(bech32_address)
    converted_data = bech32.convertbits(data, 5, 8, False)
    hex_address = ''.join([format(byte, '02x') for byte in converted_data])
    return hex_address

def confirm_transaction(txHash):
    params = {'hash':txHash}
    r = requests.get('https://api.cardanoscan.io/api/v1/transaction',params=params,headers=cardanoscanHeader)
    hexAddr = bech32_to_hex(cardanoAddress)
    transaction = r.json()
    startValue = 0
    endValue = 0
    totalInput = 0
    totalOutput = 0
    time = transaction['timestamp']
    fee = int(transaction['fees'])
    inputs = []
    outputs = []
    for sender in transaction['inputs']:
        inputs.append({'addr':sender['address'],'value':sender['value']})
    for receiver in transaction['outputs']:
        outputs.append({'addr':receiver['address'],'value':receiver['value']})

    for inp in inputs:
        if inp['addr'] == hexAddr:
            startValue += int(inp['value'])
        totalInput += int(inp['value'])
    for out in outputs:
        if out['addr'] == hexAddr:
            endValue += int(out['value'])
        totalOutput += int(out['value'])

    assert(totalInput == totalOutput+fee)
    assert(transaction['status'] == bool(True))

    transactionReport = {'totalInput': totalInput, 'totalOutput': totalOutput, 'ourTotal': endValue-startValue, 'timestamp': time}
    print(transactionReport)
    return transactionReport

def get_cardano_balance_cardanoscan(addr):#5 calls per seconds 100k/day
    res = requests.get('https://api.cardanoscan.io/api/v1/address/balance', headers=cardanoscanHeader,params={'address':addr})
    balance = res.json()['balance']
    return int(balance)

def get_cardano_price():#this can fail if i run out of free credits, or hit per minute api call limit! // 10k per month, 1 other app uses it as well, 30req/min
    #Add global tracker to mitigate this. Delete cmc and price to be sure it is 
    cmc = requests.get('https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest',headers=coinmarketcapHeader,params={'symbol':'ADA','convert':'EUR'})
    price = cmc.json()['data']['ADA'][0]['quote']['EUR']['price']
    del cmc
    return float(price)#just in case

def calculate_ADA_to_tokens(ADA_amount,ADA_to_EUR,EUR_to_TOKEN):
    actualADA = ADA_amount/1000000
    tokens = actualADA * ADA_to_EUR * EUR_to_TOKEN * 100
    return ceil(tokens) #I am so nice :)

def generate_payment_address(network=Network.MAINNET):#make test one, to not mix them up!
    psk = PaymentSigningKey.generate()
    pvk = PaymentVerificationKey.from_signing_key(psk)
    address = Address(payment_part=pvk.hash(), network=network)
    psk_json = psk.to_json()
    pvk_json = pvk.to_json()
    return str(address), psk_json, pvk_json

def get_addrs_with_balance():#i guess for now we just go trough them all?
    pass

def consolidate_funds(addrs,send_to_addr = cardanoAddress,network = Network.MAINNET):#change to PROD
    #make sure pycardano is up to date or it might fail
    from time import sleep
    context = BlockFrostChainContext(blockfrostAPI, base_url=ApiUrls.mainnet.value) #ApiUrls.preview.value ApiUrls.mainnet.value, default is preprod
    builder = TransactionBuilder(context)
    sign_keys = []
    blc = 0
    for addr in addrs:
        psk = PaymentSigningKey.from_json(addr['psk'])
        pvk = PaymentVerificationKey.from_json(addr['pvk'])
        readyAddr = Address(pvk.hash(), network=network)
        balance = get_cardano_balance_cardanoscan(addr['addr'])#5 per second MAX, we will keep it closer to 4 so that it doesn't fail, we can also change to blockfrost /w get_addr_balance()
        #balance = get_addr_preview_balance(addr['addr'])#this won't work anymore because we only have one APP
        print(f"{addr['addr']} HAS {balance/1000000} ADA",flush=True)
        sleep(0.25)
        if balance > 0:
            blc += balance
            builder.add_input_address(readyAddr)
            sign_keys.append(psk)
    if blc > 1000000:
        max_fee = max_tx_fee(context)
        print(f"MAX FEE: {max_fee} ADA")#Time to kms
        builder.add_output(TransactionOutput(Address.from_primitive(send_to_addr),Value.from_primitive([int(blc-max_fee)])))
        signed_transaction = builder.build_and_sign(signing_keys=sign_keys, change_address=send_to_addr)#we are consolidating so change goes as well
        context.submit_tx(signed_transaction)
    else:
        print(f"Too poor! {blc/1000000} ADA combined",flush=True)
    #function to consolidate all payment addresses that have balance, must be over 1ADA, hopefully would work with less

def get_addr_balance(addr):# 50k/day cca 1,5Mil/month - can do testnet stuff
    r = requests.get('https://cardano-mainnet.blockfrost.io/api/v0/addresses/'+addr,headers=blockfrostHeader)
    data = r.json()
    unit,balance = data['amount'][0]['unit'], data['amount'][0]['quantity']#check what is mainnet unit that is valid
    return int(balance)

def get_addr_preview_balance(addr):
    r = requests.get('https://cardano-preview.blockfrost.io/api/v0/addresses/'+addr,headers=blockfrostHeader)
    if r.status_code != 200:
        return 0
    print(r.json(), flush=True)
    unit, balance = r.json()['amount'][0]['unit'],r.json()['amount'][0]['quantity']
    return int(balance)

def transfer_to_preview_addr(addr,amount,network = Network.TESTNET):#Create preview app to work again, psk pvk are for app
    psk = faucetFundedAddr['psk']
    pvk = faucetFundedAddr['pvk']
    psk = PaymentSigningKey.from_json(psk)
    pvk = PaymentVerificationKey.from_json(pvk)
    address = Address(pvk.hash(), network=network)
    context = BlockFrostChainContext(blockfrostAPI, base_url=ApiUrls.preview.value)#APP IS NOT IN TESTING ANYMORE
    builder = TransactionBuilder(context)
    builder.add_input_address(address)
    builder.add_output(TransactionOutput(Address.from_primitive(addr),Value.from_primitive([int(amount)])))
    signed_tx = builder.build_and_sign([psk], change_address=address)
    context.submit_tx(signed_tx)