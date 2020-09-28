from electrum import bitcoin, crypto, ecc, util, transaction


AlicePrivateKey = "p2wpkh-p2sh:KzhKCf8xkJ15VXFVLpPqV9gyPgoL83eLQ9odqvJtJannj4yPSFgj"
JohnPrivateKey = "p2wpkh-p2sh:L2AHPXSYuPXxXKknGxEbYcu6XfvBLvtqp59L3bE1Z9q7u5JXCAPP"
LocalCoinSwapPrivateKey = "p2wpkh-p2sh:Ky4ubnS1yfYK3kPU4VfWCSW2mc9EMySVkWJwbXonrFmhtp3GejHQ"

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

JohnSecret = "b7b83b57476f5e2d0271a9acec5faab135fe4079c563a6cfc0fd6f420e61baa8"
AliceSecret = "d7a3fcaf0cfec812bb73072e14fdb678c06743823634eecf4397727e331aad5c"
DisputeReleaseSecret = "b81438795cf1a7ffd03861459cfe5e03362a908b9746d86273cf367d68cbc7f5"
DisputeRevertSecret = "aea5c425837d6a073f761c7b88284e2e5e52ff83b73b98b3c0b2f0dda868ef13"


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

EscrowAddress = bitcoin.redeem_script_to_address('p2wsh-p2sh', ESCROW_SCRIPT)
FeeAddress = bitcoin.redeem_script_to_address('p2wsh-p2sh', FEE_SCRIPT)

EscrowTx = (
    '020000000001014337eb92d28535bd3facd04a4fe1a093ab45b1b31aea0e3e59bf72516a4ca341010000001716001'
    '40316573a8b43e6ea807ad8a430ba673243e47b52ffffffff02102700000000000017a914e0dfa8050ec006ab3fb6'
    '34ac2354d2f48028984f872b581e000000000017a914585df5c7373b04f6bf64ec33e1686f2a7c1af15a870247304'
    '402200c7ea9968b43db68c41592d0509f36c161ce61b478c186a7145b790acef9e0b102206c86b8c51ab099b2bfdf'
    'f29c041b5c6769db139952043b0454dd560a37f2d3710121026de640e388dd42dc6306180d8950b8f73bf6b7fd816'
    '0735fc900c966835029ae00000000'
)

nVersion = "02000000"
Marker = "00"
Flag = "01"
nLocktime = "00000000"

TxIns = (
    "018b5f8c0ab2554f046937b1363a157737c7dd6ee6b11b42cbb78530e5a175b1"
    "c50000000023220020f8aed34c21342180422a3db5d46f94166ca556ea17f3a3"
    "e6a0cc0515772fa7e6feffffff"
)

TxOuts = (
    "01181000000000000017a91433ef3ac45a75584477a27c10cd21135da4f1ed2787"
)

TradeInstruction = "01"


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

print(Signature)

_, privkey, compressed = bitcoin.deserialize_privkey(AlicePrivateKey)
PubKey = ecc.ECPrivkey(privkey).get_public_key_hex(compressed=compressed)

print(PubKey)
print(JohnSecret)
print(TradeInstruction)
print(Script)

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

Transaction = nVersion + Marker + Flag + TxIns + TxOuts + Witness + nLocktime
print(Transaction)
