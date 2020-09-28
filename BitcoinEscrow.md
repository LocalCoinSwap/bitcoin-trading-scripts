## Trustless Bitcoin Trading - A proof by LocalCoinSwap

In less than 2 short years, LocalCoinSwap has come from a small community-founded startup, to the world's largest and most popular non-custodial P2P exchange.

As one of our founding principles is transparency, it is important that we demonstrate to our users how their funds are secured during the trading process.

Using the excellent Electrum wallet Python libraries, we will run through a full demonstration of how the non-custodial trading process works - and provide proof that your keys are always in your control when trading Bitcoin non-custodial on LocalCoinSwap.

### Running these examples

To run these examples in Python, you'll need to install the latest version of Electrum wallet on your system. While Electrum is famous as a Bitcoin wallet, it is also the most comprehensive and well-maintained Python Bitcoin library around today.

If you're a hobby rather than professional coder, we've included a short installation guide to get you started with the file `Installation.md`. If you just want to see/run the code yourself without reading the explanation we've also included `CodeDemonstration.py`.

### Bitcoin private keys on LocalCoinSwap

When you register an account with LocalCoinSwap, your browser generates a secret mnemonic phrase, which is only ever known to you. We do not store or have access to your unencrpyted mnemonic phrase, and therehore have no ability to seize or control your funds. If you have used popular webwallet applications before you will no doubt be familiar with the use of a mnemonic.

LocalCoinSwap derives your private keys from your mnemonic using the BIP39 standard, and then your address from your private keys using the P2SH(P2WPKH) format. You can export your mnemonic from your <link>settings page</link> and your individual private keys from your <link>wallet page</link> on the exchange.

We chose this format to give the benefits of SegWit with the accessibility to a regular-style Bitcoin address.

### How does a Bitcoin non-custodial trade work on LocalCoinSwap

There are 3 participants in a Bitcoin trade on LocalCoinSwap, the Buyer, the Seller, and the Arbitrator (ie: the LocalCoinSwap platform). In this example Alice is the buyer, and John is the seller.

```
AlicePrivateKey = "p2wpkh-p2sh:KzhKCf8xkJ15VXFVLpPqV9gyPgoL83eLQ9odqvJtJannj4yPSFgj"
JohnPrivateKey = "p2wpkh-p2sh:L2AHPXSYuPXxXKknGxEbYcu6XfvBLvtqp59L3bE1Z9q7u5JXCAPP"
LocalCoinSwapPrivateKey = "p2wpkh-p2sh:Ky4ubnS1yfYK3kPU4VfWCSW2mc9EMySVkWJwbXonrFmhtp3GejHQ"
```

To create the trade, Alice, John, and LocalCoinSwap created a shared escrow address, using the Bitcoin scripting language.

A Bitcoin script is a piece of code represented by an address, and once funds are sent to that address the way they can be spent is controlled by the script. Many clever things have been created with Bitcoin scripting, such as lightning network.

For the purpose of a LocalCoinSwap trade, we use a special script with the following conditions:

1. Once funds are placed in escrow, John (the seller) can release them to Alice (the buyer) at any time, but not take the funds for himself.
2. Likewise, Alice can allow John to have the funds back at any time (cancel the trade), but cannot take the funds for herself.
3. If Alice and John disagree about where the BTC should go, they can ask LocalCoinSwap to decide who is the rightful owner. LocalCoinSwap can then release the funds to Alice, or return the funds to John. However, LocalCoinSwap cannot take the funds for themselves.

A second script is used to control the trading fee BTC for LocalCoinSwap, with similar conditions.

#### Escrow script
```python
ESCROW_SCRIPT = """
OP_DUP OP_1 OP_EQUAL
OP_IF
  OP_DROP
  <AliceHashedPublicKey>
  <JohnHashedSecret>
OP_ELSE
  OP_DUP OP_2 OP_EQUAL
  OP_IF
    OP_DROP
    <AliceHashedPublicKey>
    <HashedDisputeReleaseSecret>
  OP_ELSE
    OP_DUP OP_3 OP_EQUAL
    OP_IF
      OP_DROP
      <JohnHashedPublicKey>
      <AliceHashedSecret>
    OP_ELSE
      OP_4 OP_EQUALVERIFY
      <JohnHashedPublicKey>
      <HashedDisputeRevertSecret>
    OP_ENDIF
  OP_ENDIF
OP_ENDIF
OP_ROT
OP_HASH160
OP_EQUALVERIFY
OP_OVER
OP_HASH160
OP_EQUALVERIFY
OP_CHECKSIG
""".split()
```

#### Trading fee script
```python
FEE_SCRIPT = """
OP_DUP OP_3 OP_EQUAL
OP_IF
  OP_DROP
  OP_HASH160
  <AliceHashedSecret>
  OP_EQUALVERIFY
  OP_DUP
  OP_HASH160
  <JohnHashedPublicKey>
  OP_EQUALVERIFY
  OP_CHECKSIG
OP_ELSE
  OP_DUP OP_4 OP_EQUAL
  OP_IF
    OP_DROP
    OP_HASH160
    <HashedDisputeRevertSecret>
    OP_EQUALVERIFY
    OP_DUP
    OP_HASH160
    <JohnHashedPublicKey>
    OP_EQUALVERIFY
    OP_CHECKSIG
  OP_ELSE
    OP_DUP
    OP_HASH160
    <LocalCoinSwapHashedPublicKey>
    OP_EQUALVERIFY
    OP_CHECKSIG
  OP_ENDIF
OP_ENDIF
""".split()
```

### Constructing a trade

To construct a trade, Alice and John both choose a secret, and LocalCoinSwap chooses two secrets.

The hashed verion of these secrets is baked into the escrow script, and the Bitcoin is only spendable by the someone who possess the secrets of two of the three participants in the trade. Therefore, releasing the BTC to another person is as simple as giving away your secret.

This allows LocalCoinSwap to support offline trading, which we plan to release in the future to support traders in countries such as Venezuela with difficult access to electricity.

In technical terms, a trade secret is a randomly chosen 32 byte hex string, which traders on LocalCoinSwap create automatically from their mnemonics.

```python
JohnSecret = "b7b83b57476f5e2d0271a9acec5faab135fe4079c563a6cfc0fd6f420e61baa8"
AliceSecret = "d7a3fcaf0cfec812bb73072e14fdb678c06743823634eecf4397727e331aad5c"
DisputeReleaseSecret = "b81438795cf1a7ffd03861459cfe5e03362a908b9746d86273cf367d68cbc7f5"
DisputeRevertSecret = "aea5c425837d6a073f761c7b88284e2e5e52ff83b73b98b3c0b2f0dda868ef13"
```

Now that we have the keys and secrets of all the traders, we can derive the trade variables:

```python
def HashedPublicKey(PrivKey):
    _, privkey, compressed = bitcoin.deserialize_privkey(PrivKey)
    PubKey = ecc.ECPrivkey(privkey).get_public_key_hex(compressed=compressed)
    HashedPublicKey = crypto.hash_160(bytes.fromhex(PubKey)).hex()
    return HashedPublicKey


def HashedSecret(Secret):
    HashedSecret = crypto.hash_160(bytes.fromhex(Secret)).hex()
    return HashedSecret

AliceHashedPublicKey = HashedPublicKey(AlicePrivateKey)
JohnHashedPublicKey = HashedPublicKey(JohnPrivateKey)
LocalCoinSwapHashedPublicKey = HashedPublicKey(LocalCoinSwapPrivateKey)
JohnHashedSecret = HashedSecret(JohnSecret)
AliceHashedSecret = HashedSecret(AliceSecret)
HashedDisputeReleaseSecret = HashedSecret(DisputeReleaseSecret)
HashedDisputeRevertSecret = HashedSecret(DisputeRevertSecret)
```

The fun part! We can now place these trade variables into our scripts, and then compile our scripts into raw hex code which can be interpreted by the Bitcoin runtime.

```python
Variables = [
    (AliceHashedPublicKey, '<AliceHashedPublicKey>'),
    (JohnHashedPublicKey, '<JohnHashedPublicKey>'),
    (LocalCoinSwapHashedPublicKey, '<LocalCoinSwapHashedPublicKey>'),
    (AliceHashedSecret, '<AliceHashedSecret>'),
    (JohnHashedSecret, '<JohnHashedSecret>'),
    (HashedDisputeReleaseSecret, '<HashedDisputeReleaseSecret>'),
    (HashedDisputeRevertSecret, '<HashedDisputeRevertSecret>')
]


for i in Variables:
    ESCROW_SCRIPT = [i[0] if x==i[1] else x for x in ESCROW_SCRIPT]

for i in Variables:
    FEE_SCRIPT = [i[0] if x==i[1] else x for x in FEE_SCRIPT]

def HexScript(Script):
    HexScript = ''
    for item in Script:
        if item[0:3] == 'OP_':
            opcode_int = bitcoin.opcodes[item]
            assert opcode_int < 256  # opcode is single-byte
            HexScript += bitcoin.int_to_hex(opcode_int)
        else:
            util.bfh(item)  # to test it is hex data
            HexScript += bitcoin.push_script(item)
    return HexScript

ESCROW_SCRIPT = HexScript(ESCROW_SCRIPT)
FEE_SCRIPT = HexScript(FEE_SCRIPT)
```

Now we can turn our raw Bitcoin scripts into addresses.

To save transaction fees for our users, we choose to turn these scripts into a Segwit address using P2SH(P2WSH), rather than a regular P2SH address:

```
EscrowAddress = bitcoin.redeem_script_to_address('p2wsh-p2sh', ESCROW_SCRIPT)
FeeAddress = bitcoin.redeem_script_to_address('p2wsh-p2sh', FEE_SCRIPT)
```

This process is how all the escrow and fee addresses used during LocalCoinSwap trading are constructed. If you don't trust us, just click the `expert` box in a trade to see the variables - which you can then use to double-check the escrow addresses match the scripts provided above. Non-custodial means you don't need to take our word for any part of the process.

Now that we have our addresses, John can begin sending BTC to them. Once BTC is placed in the addresses, it can only leave the addresses according to the conditions of the scripts above.

For the purpose of this demonstration, we've made a real transaction into the escrow address from John:
```python
EscrowTx = (
    '020000000001014337eb92d28535bd3facd04a4fe1a093ab45b1b31aea0e3e59bf72516a4ca341010000001716001'
    '40316573a8b43e6ea807ad8a430ba673243e47b52ffffffff02102700000000000017a914e0dfa8050ec006ab3fb6'
    '34ac2354d2f48028984f872b581e000000000017a914585df5c7373b04f6bf64ec33e1686f2a7c1af15a870247304'
    '402200c7ea9968b43db68c41592d0509f36c161ce61b478c186a7145b790acef9e0b102206c86b8c51ab099b2bfdf'
    'f29c041b5c6769db139952043b0454dd560a37f2d3710121026de640e388dd42dc6306180d8950b8f73bf6b7fd816'
    '0735fc900c966835029ae00000000'
)
```

Any ordinary transaction which funds the escrow address will work, you can check out our example here:
https://blockchair.com/bitcoin/transaction/c5b175a1e53085b7cb421bb1e66eddc73777153a36b13769044f55b20a8c5f8b

Once John has placed the BTC in the escrow address, Alice will make the payment for the BTC in her local currently directly to John. Both parties can feel safe, as the BTC is safely secured during this process.

### Ending a trade

Assuming that John has received the funds from Alice, he now gives Alice his secret. Alice is now in possession of Johns secret, and can combine this with a signature from her private key to spend the funds from the escrow address.

We will now show how to construct a transaction for Alice which spends funds from the escrow address.

At its most basic level a valid Bitcoin (SegWit) transaction is just a bunch of things added together:
`Transaction = nVersion + Marker + Flag + TxIns + TxOuts + Witness + nLocktime`

#### Variables from the transaction formula

`nVersion`, `Marker`, `Flag` and `nLocktime`:
These variables are generic to almost all Bitcoin transactions, and the same each time.

```python
nVersion = "02000000"
Marker = "00"
Flag = "01"
nLocktime = "00000000"
```

`Txins`:
These are the details of the funding transactions into the escrow address which we are spending.
```python
TxIns = (
    "018b5f8c0ab2554f046937b1363a157737c7dd6ee6b11b42cbb78530e5a175b1"
    "c50000000023220020f8aed34c21342180422a3db5d46f94166ca556ea17f3a3"
    "e6a0cc0515772fa7e6feffffff"
)
```

`TxOuts`:
These are the details of Alices addresses the escrow funds are being sent to, created using Alices address, and the amount we wish to spend.
```python
TxOuts = (
    "01181000000000000017a91433ef3ac45a75584477a27c10cd21135da4f1ed2787"
)
```

A detailed explanation of serialising `TxIns` and `TxOuts` is beyond the scope of this demonstration. However, it's rather simple, and you can find a full explanation here:
https://en.bitcoin.it/wiki/Transaction

`Witness`:
This final piece is the crucial part, containing the variables which are used to unlock the Bitcoin scripts which control the escrow.

You can think of the Witness as the variables which are plugged into the Bitcoin script, in order to "unlock" it. If the variables are correct, the script is unlocked and the transaction is valid. If the variables are incorrect, the BTC cannot be spent by the rules of the blockchain.

To construct a valid Witness, Alice needs 5 things:

1. A signature of the entire rest of the transaction with her private key, to prove that she approves the spending of the inputs to the chosen outputs. The specifications of this signature can be found here:
https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki
2. Her public key
3. The secret she recieved from John
4. Her chosen trade instruction (In this case `01` to release)
```python
TradeInstruction = "01"
```
5. Finally, the compiled Bitcoin escrow script we created earlier

Once Alice has these 5 things, she can serialise them (add them together with some extra bytes to specify the length) into the `Witness` and complete the transaction.

We already have all these items except for the signature, which we can use Electrum to create

```python
def SignatureBIP143(
        ToAddress, ToValue, FromValue, PrevHash, PrevIdx, Script, Priv
    ):
    txOutput = transaction.TxOutput.from_address_and_value(ToAddress, ToValue)
    tx = transaction.PartialTransaction()
    tx.add_outputs([txOutput])        
    prevout = transaction.TxOutpoint(bytes.fromhex(PrevHash), PrevIdx)
    txInput = transaction.PartialTxInput(prevout=prevout)
    txInput._trusted_value_sats = FromValue
    txInput.witness_script = bytes.fromhex(Script)
    tx.add_inputs([txInput])
    Sig = tx.sign_txin(0, bitcoin.deserialize_privkey(Priv)[1])
    return Sig

ToAddress = "36RcyHftoD6amAk41VfjPiQiGcVcASB7Q4" # Alices address
ToValue = 4120 # Value of funding transaction minus a fee for the miners
FromValue = 10000
PrevHash = "c5b175a1e53085b7cb421bb1e66eddc73777153a36b13769044f55b20a8c5f8b"
PrevIdx = 0
Script = ESCROW_SCRIPT
Priv = AlicePrivateKey

Signature = SignatureBIP143(
    ToAddress, ToValue, FromValue, PrevHash, PrevIdx, Script, Priv
)
```

We now have all the variables needed for the witness:

```
print(Signature)

_, privkey, compressed = bitcoin.deserialize_privkey(AlicePrivateKey)
PubKey = ecc.ECPrivkey(privkey).get_public_key_hex(compressed=compressed)

print(PubKey)
print(JohnSecret)
print(TradeInstruction)
print(Script)
```
```
3044022023e084b3853df0b30009f036782b6541ee3fdaea825ef69a6ef4984c60de694402200c1114656c10011f1f38bb360c1a7b83a955e5ca9b3a4bf88f248d3a593de34101

02ebe992c96ac746e1032a21372a031a0e07b7a718af750e6ee1a92e233b90a1cf

b7b83b57476f5e2d0271a9acec5faab135fe4079c563a6cfc0fd6f420e61baa8

01

765187637514e1e95151fa5ad640fd82629712633ab1c3c1f79a14df0fcf0b589f087c958f2b7b2536784af9e1a46167765287637514e1e95151fa5ad640fd82629712633ab1c3c1f79a14bee33af6fb798e836de7282a760df30281efc6906776538763751472b30bbc34d451f9f3cd120653a7a8b5ded3fc031454f334cbcd53174739cffa83745c2439300b19776754881472b30bbc34d451f9f3cd120653a7a8b5ded3fc0314a50a9dda27d0155ef7c0a03ecb4ff8819372095a6868687ba98878a988ac
```

Adding these all together we get:

```python
Witness = (
    "05" # Length of witness
    "47" # Length of signature
    + Signature + \
    "21" # Length of public key
    + PubKey + \
    "20" # Length of Johns secret
    + JohnSecret + \
    "01" # Length of trade instruction
    + TradeInstruction + \
    "c6" # Length of Bitcoin script
    + Script
)
```

Which gives us our final transaction:

```python
Transaction = nVersion + Marker + Flag + TxIns + TxOuts + Witness + nLocktime
print(Transaction)
```
```
020000000001018b5f8c0ab2554f046937b1363a157737c7dd6ee6b11b42cbb78530e5a175b1c5000000002322002
0f8aed34c21342180422a3db5d46f94166ca556ea17f3a3e6a0cc0515772fa7e6feffffff01181000000000000017
a91433ef3ac45a75584477a27c10cd21135da4f1ed278705473044022023e084b3853df0b30009f036782b6541ee3
fdaea825ef69a6ef4984c60de694402200c1114656c10011f1f38bb360c1a7b83a955e5ca9b3a4bf88f248d3a593d
e341012102ebe992c96ac746e1032a21372a031a0e07b7a718af750e6ee1a92e233b90a1cf20b7b83b57476f5e2d0
271a9acec5faab135fe4079c563a6cfc0fd6f420e61baa80101c6765187637514e1e95151fa5ad640fd8262971263
3ab1c3c1f79a14df0fcf0b589f087c958f2b7b2536784af9e1a46167765287637514e1e95151fa5ad640fd8262971
2633ab1c3c1f79a14bee33af6fb798e836de7282a760df30281efc6906776538763751472b30bbc34d451f9f3cd12
0653a7a8b5ded3fc031454f334cbcd53174739cffa83745c2439300b19776754881472b30bbc34d451f9f3cd12065
3a7a8b5ded3fc0314a50a9dda27d0155ef7c0a03ecb4ff8819372095a6868687ba98878a988ac00000000
```

We can then broadcast this transaction using most wallets, or an online broacaster (such as https://www.blockchain.com/btc/pushtx)

Our final transaction on the blockchain:
https://blockchair.com/bitcoin/transaction/2deaf3031fa7b042a83c13a48512f8b22df6bd49cc24178162984141263cbe94