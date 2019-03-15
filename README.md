# GopherCoin
## A very simple Blockchain

**DISCLAIMER:** This is by no means a production ready blockchain/cryptocurrency and should not be used as such. For now, this is just the basic infrastucture for the server and client backend. This project was built soley as a means of introducing myself to Python as well as gaining a better understanding of how blockchains function. It is in no way operational at this point. But it was super fun to learn and I plan to continue to work on it!

I followed this incredibly well detailed guide by Adil Moujahid: [A Practical Introduction to Blockchain with Python](http://adilmoujahid.com/posts/2018/03/intro-blockchain-bitcoin-python/) and was helped along the way with the aid of Chris Angelico who you can find here: https://github.com/Rosuav

**TO-DOs:**
 - [ ] Build web portal
 - [ ] Identify Miners by wallet rather than node.id so they are properly rewarded
 - [ ] Check wallets to make sure users have enough coin for their transactions
 - [ ] Check Transaction records for signature matching
 - [ ] Require verification of public-keys for from network peers for transactions
 - [ ] Change mining to POST with proof-of-work input, garnered from victory in small online game, **Gophergeddon**, my next planned side project.

## How to use this code

I would first recomend doing some reading to get a basic grasp of what a blockchain is, especially cryptocurrencies, and how mining works from a high level. I don't have the space here to go too in depth and people with a better understanding than me have written about them extensively. The objective of my work here is to look at how these processes actually happen in code. I found this website to be pretty helpful if you're looking for somewhere to start: (https://www.bitcoinmining.com/). Secondly, I tried to be as detailed as possible in my write-up below, but if you run into any issues or have any questions, please feel free to ask! I'm really looking forward to making a simple front-end for this which should help to make things a little more clear.

### SETUP
  1. clone repo
  2. `cd` into the folder
  3. From the terminal run `python -m pip install -r requirements.txt` to install necessarry frameworks/libraries
  4. To really take full advantage of peeking under the hood of how this or any blockchain works, you'll need to have two nodes accessing the same server. If you haven't done this before, it is fairly straight forward. You just need to run the code from two different ports on your machine, which I've included as an argument when running the file as `-p` or `--port` flag. To do this:
     * Run `python blockchain.py -p 5000` in your terminal. 
     * Then open a new terminal window, navigate to your cloned directory once again, and run `python blockchain.py -p 5001`

### USING THE BLOCKCHAIN

  You should now have two seperate nodes up and running on your very own local blockchain! From here you can perform most but not all of your basic functionality. Because I do not have a frontend built yet, for the next steps you're going to need an API development Environment. You can do this from your terminal with cURL if you'd like but for clarity and ease of use I highly reccomend using [Postman](https://www.getpostman.com/). 

  First, let's mine a block or two. Setup Postman with the following info:

  - GET: `http://localhost:5000/mine`

    ![mining step 1](/READme-images/mining0.png)
  
 **You should get a response that looks something like this:**

    ![mining step 2](/READme-images/mining0-response.png)

  Mining a block is very similar to a transaction between two people, except that the sender is the blockchain authority/server. Each block will contain data specific to that chain:
  * It's index in the chain
  * The hash of the previous block
  * The proof that it used to solve the blockchain Proof of Work
  * A list of transactions, including the action of being mined as well as any other transactions that have occured within the blockchain networek since the last block was mined.

  Now go over to your other port/node and do some mining over there until its chain is longer than your first chain. I found it easiest to do this in multiple tabs within Postman:
  - Run the GET: http://localhost:*5001*/mine a few times and see how the hash, index, and hash all change to reflect the growing chain.
  - If you're curious, check out the `/chain` endpoint to see the full chain: GET: http://localhost:5001/chain

  ![chain](/READme-images/chain.png)

  Now you may start to see the most basic issue with a dispersed network currency. These two seperate nodes are working on the same chain, at the same time and now have differing data. What are we to do?! *Concensus to the rescue!*
    - Hop on over back to your original node `localhost:5000` 
    - And send a `POST` request to `http://localhost:5000/nodes/register` with the following info in the body as JSON:
      ```{
	          "nodes": ["http://127.0.0.1:5001"]
         }```
    
  ![register](register.png)
    
  You should get a response back that looks something like this:
  ![register response](register-response.png)

  Our blockchain will now know that when we issue a resolve command, it should check the chain on node on `localhost:5001` against it's own, if you had multiple ports open and registered all of them, our blockchain would go through each one and run a check. Let's see what that looks like
    - Send a `GET` request to `http://localhost:5000/nodes/resolve`
    - Which will return a message that says whether or not the chain was replaced as well as the current chain, in our case the chain that had been existing on the node at our 5000 port was outdated and as such was replaced with the chain from port 5001:
    ![resolve](resolve.png)

  For this simple blockchain, our concensus alogrithm measures the total size/length of the chain to see which one should reign supreme. Bitcoin however determines 'longest' chain s the chain which ends in the block that has solved the most difficult proof-of-work algorithm and sets that chain as the correct one. This could potentially lead to some overwriting of blocks and often does in a simple blockchain like ours. Bitcoin however only has a new block mined once about every 10 minutes, so the liklihood of people operating on an outdated chain or having their blocks overwritten is slim enough to not be an issue.

  Our last bit of functionality has to do inter-person transactions. That is to say, what if I have some gopher-coins I've mined and would like to buy a good from a retailer that accepts gopher-coin as a curren$$y *please no one do this in real life*. For this you will need to spin up our client side backend:
    - back in the terminal run `python client.py -p 8080`
    - Get a new wallet, which will consist of public and private keys generated as 1024 bit RSA keys. To do this jump back in postman and send a `GET` request to `http://localhost:8080/wallet/new` which should give you a response akin to:
    ![wallet](wallet.png)
    
  Your public key also serves as your wallet ID. This is very common practice amongst functioning cryptocurrencies. You should not however, share your private key with anyone or post it online anywhere... ever. This would provide anyone with the ability to decrypt your public key and perform transactions on your account and steal all your precious Gopher Coin! But you will need to provide it when you initiate a transaction. The private key will never be included in any response from the system. Instead, a transaction signature is sent back which you will include when you register the transaction with the server. Let's see what initiating a transaction looks like:
    - On your client send a `POST` request to `http://localhost:8080/transactions/generate` with the following inputs filled out in the body as JSON:
      * "sender": *your public key*
      * "sender-private-key": *your private key*
      * "recipient": *the public key/wallet ID of someone else*
      * "amount": *how many previous GopherCoins are you willing to part with*
      ![generate transaction](gen-transaction.png)
    - You should get a response back from the client confirming the information you provided as well as the signature you will use to register the transaction with the blockchain. If any of the fields were filled out incorrectly or left blank you'll receive an error.
    ![transaction response](transaction-response.png)
    
  The last step is to register your transaction with the blockchain network. It will be added to the next block to be mined and when that occurs, the transaction can be verified via the signature and will process.
    - back on port:5000 `POST` to `http://localhost:5000/transactions/new` with the following info
      * "signature": *provided to you in the response from the system when you generated the transaction*
      * "amount": *matching the amount from the original order*,
      * "recipient": *again, match what you sent in the transaction issued*
      * "sender": *your public key*
    - the system should respond letting you know what block the transaction will be recorded to, feel free to go mine that block to get some more piping hot GopherCoin and see the transaction in the network records!
    ![register transaction](reg-transaction.png)

That's it! Thanks for reading through this wall of text and again let me know if you have any questions. I had a lot of fun building this project base and I look forward to improving upon it in the future.
