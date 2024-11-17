# Memecoin Scanner - Installation Guide 🚀

This guide will help you set up and run the Solana Memecoin Scanner on your MacBook Pro. Don't worry if you're not technical - we'll go through this step by step!

## Prerequisites

- A MacBook Pro
- Internet connection
- CoinMarketCap API key (I'll show you how to get this)

## Step 1: Install Python 📥

1. Open Terminal (you can find it by pressing Command + Space and typing "Terminal")
2. Copy and paste this command to install Homebrew (a software installer for Mac):
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
3. After Homebrew is installed, install Python by typing:
```
brew install python
```

## Step 2: Get Your CoinMarketCap API Key 🔑

1. Go to [CoinMarketCap](https://coinmarketcap.com/api/)
2. Click "Get Your API Key Now"
3. Sign up for a free account
4. Once logged in, copy your API key from the dashboard

## Step 3: Set Up the Project 🛠️

1. Create a new folder on your desktop called "memescanner"
2. Save the Python script I sent you in this folder as `scanner.py`
3. Open Terminal again
4. Type these commands one by one:
```
cd ~/Desktop/memescanner
python -m pip install requests tabulate termcolor
```

## Step 4: Add Your API Key 🔐

1. Open the `scanner.py` file (you can use TextEdit)
2. Find this line near the top: `api_key = "INSERT_YOUR_API"`
3. Replace `INSERT_YOUR_API` with your CoinMarketCap API key
4. Save the file

## Step 5: Run the Scanner 🏃‍♂️

1. In Terminal (make sure you're still in the memescanner folder), type:
```
python scanner.py
```

The scanner will start running and show you trending Solana memecoins! 

## Troubleshooting 🔧

If you see any errors:
- Make sure you're in the right folder (Desktop/memescanner)
- Check that you've properly copied your API key
- Try running the pip install command again

## Usage Tips 💡

- The scanner shows coins with:
  - Volume over $50,000
  - Price increase between 20% and 300% in 24h
  - Only Solana-based tokens
- The results are color-coded:
  - Green = positive change
  - Red = negative change
- You'll see both a summary table and detailed info for the top 5 coins
