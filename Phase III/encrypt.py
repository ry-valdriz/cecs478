# import cryptography
# from cryptography import Fernet
import Crypto, json
from base64 import b64encode, b64decode
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad,unpad
from Crypto.Random import get_random_bytes
from Crypto.Hash import HMAC, SHA256

def encryptAES(message, key_AES):
    message = message.encode('utf-8')#convert to bytes to use in AES encryption function
    cipher_AES = AES.new(key_AES, AES.MODE_CBC) #initialize AES object
    iv = b64encode(cipher_AES.iv).decode('utf-8') #conver iv from bytes to string
    cipherText_Message_Bytes = cipher_AES.encrypt(pad(message, 128)) #encrypt message
    print('iv : ', iv)
    print('iv length: ', len(iv))
    return cipherText_Message_Bytes

def encryptRSA(publicKeyFile, keys_bytes): #change to PGP
    publicKey = RSA.generate(2048) #generate rsa key object
    publicKey = RSA.import_key(publicKeyFile.read()) #create rsa public key object
    cipher_rsa = PKCS1_OAEP.new(publicKey) #create rsa cipher object
    return cipher_rsa.encrypt(keys_bytes)

def decryptRSA(privateKey, RSA_ciphertext):
    cipher_rsa = PKCS1_OAEP.new(privateKey) #create rsa cipher object
    return cipher_rsa.decrypt(RSA_ciphertext)


def createHMAC(key_HMAC):
    return HMAC.new(key_HMAC, digestmod=SHA256) #instantiate hmac object


def encryptMessage(publicKeyAddress, message): #encryption function
    print('Encrypting. . . . . . . . . . . . . . . . . .')
    
    #create file object for public key
    publicKeyFile = open(publicKeyAddress, 'rb')

    #print('contents of public key: ' + '\n', publicKeyFile.read())
    
    key_AES = get_random_bytes(32) #generate 256 bit key for AES
    key_HMAC = get_random_bytes(32) #256 bit key for HMAC
    print('key_HMAC before b64encode: ', key_HMAC)
    print('key_AES before b64encode: ', key_AES)

    cipherText_Message_Bytes = encryptAES(message, key_AES) #encrypt message with AES
   
    h = createHMAC(key_HMAC) #HMAC object

    print('print cipher text in bytes: ', cipherText_Message_Bytes)
   
    # keys_bytearray = bytearray(key_AES) #copy aes key to bytearray
    # keys_bytearray.append(key_HMAC) #append hmac key to keys_bytearray
    ka = b64encode(key_AES).decode('utf-8') #string of aes key
    print('AES key length: ', len(ka))
    print('AES key: ',ka)


    kh = b64encode(key_HMAC).decode('utf-8') #string of hmac key
    print('hmac key length: ', len(kh))
    print('HMAC key: ',kh)

    k = ka + kh #concatenate the two keys
    print('Concatenated Keys:', k) #test
    print('concatenated keys length:', len(k))

    
    keys_bytes = k.encode('utf-8') #convert back to bytes
    print('key_bytes: ', keys_bytes)
    print('key_bytes.decode: ', keys_bytes.decode())

    cipherText_Keys_Bytes = encryptRSA(publicKeyFile, keys_bytes) #encrypt AES and HMAC keys with rsa encryption
    cipherText_Keys_String = b64encode(cipherText_Keys_Bytes).decode('utf-8')

    print('Encrypted keys:' , cipherText_Keys_String ) #print out AES and HMAC keys concatenated and encrypted

    cipherText = b64encode(cipherText_Message_Bytes).decode('utf-8') #convert cipher text from bytes to string

    #h.update(cipherText.encode('utf-8')) #authenticate the message
    h.update(cipherText_Message_Bytes)

    HMAC_tag = h.hexdigest()
    print('HMAC tag during encryption:', HMAC_tag) #print out hmac tag of the authenticated message

    
    try: #check if verify works during encryption
        h.hexverify(HMAC_tag)
        print('the message is authentic')
    except ValueError:
        print('The message or key is wrong')
    

    
    JSON_output = json.dumps({'AES_ciphertext' : cipherText, 'RSA_ciphertext' : cipherText_Keys_String, 'HMAC_Tag' : HMAC_tag }) 
    
    print('ciphertext during encryption: ', cipherText)
    print('encrypted keys during encryption: ', cipherText_Keys_String)
    print('hmac tag  encryption: ', HMAC_tag)
    print('AES Key: ', ka)
    print('HMAC Key: ',kh)

    #print(JSON_output)
    outfile = open("Testing.encrypt", "w")
    outfile.write(JSON_output)
    outfile.close()



    return JSON_output #return json object containing encrypted keys, ciphertexts, and HMAC tag
    

def decryptMessage(privateKeyAddress, JSON_output):
    print('Decrypting. . . . . . . . . . . . . . . . .')

    jsonFile = json.loads(JSON_output)

    AES_ciphertext = jsonFile['AES_ciphertext']

    #AES_ciphertext = b64decode(jsonFile['AES_ciphertext']) #need it in bytes for HMAC
    #RSA_ciphertext = jsonFile['RSA_ciphertext']
    RSA_ciphertext = b64decode(jsonFile['RSA_ciphertext']) #encrypted keys
    HMAC_tag = jsonFile['HMAC_Tag']
    print('hmac_tag_encryption in decryption: ', HMAC_tag)

    
    privateKeyFile = open(privateKeyAddress, 'rb')
    privateKey = RSA.generate(2048) #generate rsa key object
    privateKey = RSA.import_key(privateKeyFile.read()) #create rsa private key object

    print('AES ciphertext during decryption: ', AES_ciphertext)
    print('RSA ciphertext during decryption: ', RSA_ciphertext)

    keys_plaintext = decryptRSA(privateKey, RSA_ciphertext)
    
    #test
    #keys_plaintext.decode('utf-8')
    
    #print('RSA_ciphertext length decryption: ', len(RSA_ciphertext))
    key_AES = keys_plaintext[0:43]
    key_HMAC = keys_plaintext[44:87]

    print('aes key during decryption', key_AES)
    print('HMAC key during decryption', key_HMAC)
    #print('AES_Key: ', AES_key)
    #print(AES_ciphertext)

    #HMAC_key.decode('utf-8') #change to byte string for HMAC
    hm = createHMAC(key_HMAC)
    
    hm.update(AES_ciphertext.encode('utf-8'))

    print('hmac tag during decryption', hm.hexdigest())

    # if hm.verify(HMAC_tag.encode('utf-8')):
    #     print('mac tag is authentic')
    # else:
    #     print('message or key is wrong')
    
    try:
        hm.hexverify(HMAC_tag)
        print('the message is authentic')
    except ValueError:
        print('The message or key is wrong')
    

    return


#MAIN FUNCTION
publicKeyAddress = input('Please enter the address of your public key: ')
message = input('Please enter message to encrypt:')

JSON_output = encryptMessage(publicKeyAddress, message)

privateKeyAddress = input('Please enter the address of your private key: ')

decryptMessage(privateKeyAddress, JSON_output)









