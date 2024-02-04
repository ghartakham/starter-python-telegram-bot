import requests
import time
import os

s = requests.Session()

base_headers = {
	'User-Agent':	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
	'Referer':	'https://app.landr.com/',
	'authorization':	'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImd0eSI6WyJhdXRob3JpemF0aW9uX2NvZGUiXSwia2lkIjoic3pSUGRiamZmQlVicTY0UkpVWE0tTWpqYkV3In0.eyJhdWQiOlsiYXBpLmxhbmRyLmNvbSIsIjE2MTI5YzY3LTU4M2YtNDcwNy04N2QzLWViN2U4Mzc1ZWFmMyJdLCJleHAiOjE3MDcxMjQ0MDYsImlhdCI6MTcwNzAzODAwNiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5sYW5kci5jb20vIiwic3ViIjoiNzA2NjZhNWUtMWIxZS00Njc2LThlNzItYzYwZWVjN2Q4NTJkIiwianRpIjoiMDBhM2EzMzctMmQ2MS00NDRiLTlhYTctYjMwZjAwN2NlYjM4IiwiYXV0aGVudGljYXRpb25UeXBlIjoiR09PR0xFIiwiZW1haWwiOiJlc2VyYW5vdW1pcmF0QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhcHBsaWNhdGlvbklkIjoiMTYxMjljNjctNTgzZi00NzA3LTg3ZDMtZWI3ZTgzNzVlYWYzIiwic2NvcGUiOiJvcGVuaWQrb2ZmbGluZV9hY2Nlc3MiLCJyb2xlcyI6W10sImF1dGhfdGltZSI6MTcwNzAzODAwNiwidGlkIjoiOTcxMjdjZDMtY2MyOC00ZmMwLWFkMDAtYjE2NjlhMzhlODY1IiwiaHR0cHM6Ly9hcGkubGFuZHIuY29tL25hbWVpZCI6IjcwNjY2YTVlLTFiMWUtNDY3Ni04ZTcyLWM2MGVlYzdkODUyZCIsImh0dHBzOi8vYXBpLmxhbmRyLmNvbS91c2VyX25hbWUiOiJlc2VyYW5vdW1pcmF0QGdtYWlsLmNvbSJ9.VBQJ_g36VM9DvFMlHSNj4bPS-QLACr9EwPEOmLHONpBC4uEH7wRRDR3z_h3zDWZ-faYCHTB3M4eosW0mHnc2i1RXAw3lfnC7l32IkPyYvH6aQzIQ68FhWduQ_jm-pWnmtJn7381Vdn3lNZLHX_it1qNKW3iZ0cj-8bBdGJFrtJRhJ96hDvOkhom3CicrniSz4pqpkavbuYJ3c61v-KbbM5Z1IcRLwvheyqPHYKSE9xnepqp699S1mcYkRXoRWxfo35YAUh9NoL34Q-EsUH_M8bZNoSLION0JI_2gDkAVWH_5n4mmEDwn06-udMTW6tpfuQeXR5TxR0-MYaQu93_JGw',
	'x-landr-client':	'version=2.19.0, kind=Mastering'	
}

s.headers.update(base_headers)

def upload_file(file_path):

	file_name = os.path.basename(file_path)

	json_data = {
		"operationName": "createAssetMultipartUpload",
		"variables": {
			"input": {
				"fileName": file_name,
				"isMaster": True,
				"interactionSource": "New Action - Master"
			}
		},
		"query": "mutation createAssetMultipartUpload($input: CreateAssetMultipartUploadInput!) {\n  createAssetMultipartUpload(input: $input) {\n    assetId\n    uploadId\n    __typename\n  }\n}"
	}

	r = s.post('https://api3.landr.com/core-bff-v2/?operationName=createAssetMultipartUpload', json=json_data)
	data = r.json()['data']['createAssetMultipartUpload']
	asset_id = data['assetId']
	upload_id = data['uploadId']


	json_data = {
		"operationName": "prepareUploadPart",
		"variables": {
			"input": {
				"number": 1,
				"uploadId": upload_id
			}
		},
		"query": "query prepareUploadPart($input: PrepareUploadPartInput!) {\n  prepareUploadPart(input: $input) {\n    uploadUrl\n    headers {\n      authorization\n      amzDate\n      __typename\n    }\n    __typename\n  }\n}"
	}

	r = s.post('https://api3.landr.com/core-bff-v2/?operationName=prepareUploadPart', json=json_data)

	data = r.json()['data']['prepareUploadPart']
	upload_url = data['uploadUrl']
	amz_headers = data['headers']

	upload_headers = {
		'User-Agent': base_headers['User-Agent'],
		'Referer': base_headers['Referer'],
		'Origin':	'https://app.landr.com',
		'authorization': amz_headers['authorization'],
		'x-amz-date': amz_headers['amzDate'],
		'Sec-Fetch-Site':	'cross-site',
		'Sec-Fetch-Mode':	'cors',
		'Sec-Fetch-Dest':	'empty'
	}


	with open(file_path, 'rb') as f:
		r = s.put(upload_url, data=f, headers=upload_headers)

	etag = r.headers['ETag']
	return upload_id, asset_id, etag


def complete_upload(upload_id, etag):
	json_data = {
		"operationName": "completeMultipartUpload",
		"variables": {
			"input": {
				"parts": [{
					"partNumber": 1,
					"eTag": etag
				}],
				"uploadId": upload_id
			}
		},
		"query": "mutation completeMultipartUpload($input: CompleteMultipartUploadInput!) {\n  completeMultipartUpload(input: $input) {\n    uploadId\n    __typename\n  }\n}"
	}

	s.post('https://api3.landr.com/core-bff-v2/?operationName=completeMultipartUpload', json=json_data)


def get_mastering_samples(asset_id):
	json_data = {
	"operationName": "GetPreviewAssetModalData",
	"variables": {
		"assetId": asset_id
	},
	"query": "query GetPreviewAssetModalData($assetId: ID!) {\n  assetStandardMasteringPreview(assetId: $assetId) {\n    ...AssetStandardMasteringPreviewFragment\n    __typename\n  }\n  assetById(assetId: $assetId) {\n    id\n    name\n    type\n    audioInfo {\n      duration\n      format\n      __typename\n    }\n    __typename\n  }\n  libraryStatistics {\n    hasReferences\n    __typename\n  }\n}\n\nfragment AssetStandardMasteringPreviewFragment on AssetStandardMasteringPreview {\n  __typename\n  id\n  isLowQuality\n  isTooLoud\n  engineVersion\n  originalSample {\n    mp3Url\n    trackNames\n    __typename\n  }\n  masterSamples {\n    intensity\n    mp3Url\n    style\n    versionWithRecipeSettingsExists\n    volumeRatio\n    __typename\n  }\n}"
	}

	attempts = 0
	while True:
		r = s.post('https://api3.landr.com/core-bff-v2/?operationName=GetPreviewAssetModalData', json=json_data)
		data = r.json()

		if data['data']:
		    mastering_preview = data['data']['assetStandardMasteringPreview']
		    master_samples = mastering_preview['masterSamples']
		    
		    for sample in master_samples:
		        if sample['mp3Url']:
		            return master_samples
		else:
			attempts += 1

		if attempts == 2:
			return None

		time.sleep(5)

def delete_asset(asset_id):
	json_data = {
		"operationName": "deleteAssets",
		"variables": {
			"assets": [{
				"assetId": asset_id,
				"type": "Audio"
			}]
		},
		"query": "mutation deleteAssets($assets: [AssetIdentification!]!) {\n  deleteAssets(assets: $assets) {\n    deletedAssets\n    __typename\n  }\n}"
	}

	s.post('https://api3.landr.com/core-bff-v2/?operationName=deleteAssets', json=json_data)
