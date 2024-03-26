import uvicorn

if __name__ == '__main__':
    uvicorn.run('cdkproxymain:app', host='127.0.0.1', port=2805, log_level='info', reload=True)
