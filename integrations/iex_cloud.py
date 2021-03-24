import secured.iex_cloud as secured
import requests


base_url = "https://sandbox.iexapis.com/"
version = "stable/"
my_token = secured.my_token



def get_standard_deviation(symbol):

    url = base_url+version+'stock/'+symbol+'/indicator/stddev'
    response = requests.get(url=url,params={'token':my_token,'range':'1m','lastIndicator': True, 'indicatorOnly': True})
    json_response = response.json()
    return json_response['indicator'][0][0]


