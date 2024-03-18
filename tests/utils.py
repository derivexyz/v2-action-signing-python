import requests


def order_debug():
    """
    Return all live ETH option tickers and extract sub_id.
    """
    url = "https://api-demo.lyra.finance/private/order_debug"
    payload = {}
    response = requests.post(
        url, json=payload, headers={"accept": "application/json", "content-type": "application/json"}
    )
    results = response.json()["result"]
    print(len(results))

    # choose a random live instruments
    random_index = random.randint(0, len(results) - 1)

    print(results[random_index])

    return results[random_index]
