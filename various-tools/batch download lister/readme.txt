Since flutter cannot do native zipcrypto and beautifulSoup shenanigans, I opted to pre-compute the list of files that the downloader should take.

Place this script with the `pak` files and run. It will generate 3 json files, one for `common` (stages), one for `android` (ogg), and one for `ios` (m4a). 

Move these files to api/config.

The flutter app will simply query the endpoint and use the list to download.