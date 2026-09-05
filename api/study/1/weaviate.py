import weaviate
from weaviate.auth import AuthApiKey


client = weaviate.connect_to_wcs(
    cluster_url= "3vso7l7etfojtkhajo3pbw.c0.asia-southeast1.gcp.weaviate.cloud",
    auth_credentials=AuthApiKey("UW5PdkN0bDVFQURnd05OTl9qT2djd2o5VmNWd1QyK1BWM1NrSWFZWXRIcWhPOTdxdlNUa083eVFYSlVRPV92MjAw")

)