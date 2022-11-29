import asyncio 

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
import json

from Logic.DataframeLogic import DataframeLogic
from Models.RequestItemModel import Item
from Data.DbContext import Context

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

dflogic = DataframeLogic()

with open("config.json") as file:
    config = json.load(file)

datalake_account_access_key = config['datalake']['datalake_account_access_key']
datalake_container = config['datalake']['datalake_container']
datalake_container2 = config['datalake']['datalake_container2']
datalake_account_name = config['datalake']['datalake_account_name']

context = Context(config['database']['server'], config['database']['database'], config['database']['username'], 
    config['database']['password'], config['database']['driver'])

df_og = pd.read_csv(f'abfs://{datalake_container}@{datalake_account_name}.dfs.core.windows.net/Producto_Unico.csv',storage_options = {'account_key': datalake_account_access_key})
df2_og = pd.read_csv(f'abfs://{datalake_container}@{datalake_account_name}.dfs.core.windows.net/Producto_Sucursales.csv',storage_options = {'account_key': datalake_account_access_key})
df_cat = pd.read_csv(f'abfs://{datalake_container}@{datalake_account_name}.dfs.core.windows.net/dboCategoria.csv',storage_options = {'account_key': datalake_account_access_key})
df_subcat = pd.read_csv(f'abfs://{datalake_container}@{datalake_account_name}.dfs.core.windows.net/dboSubCategoria.csv',storage_options = {'account_key': datalake_account_access_key})

@app.get("/productos")
async def getProductos(ignoreEmpty: bool = False):
    '''Devuelve todos los productos'''
    # Lee dataframes y variables 
    df = df_og.copy()

    # Si el query parameter ignoreEmpty es true entonces ignora las sucursales vacias
    if ignoreEmpty:
        df2 = df2_og[df2_og['Stock'] != 0].copy()
    else:
        df2 = df2_og.copy()
    
    # Devuelve dataframe filtrado
    join = dflogic.filterDataframes(df,df2)

    return json.loads(join.to_json(orient='records'))


@app.get("/producto/{id_producto}")
async def getProductoById(id_producto: int, response: Response, ignoreEmpty: bool = False):
    '''Devuelve el producto que tenga cierto ID'''
    # Lee dataframes
    df = df_og.copy()

    # Si el query parameter ignoreEmpty es true entonces ignora las sucursales vacias
    if ignoreEmpty:
        df2 = df2_og[df2_og['Stock'] != 0].copy()
    else:
        df2 = df2_og.copy()

    # Filtra por el producto pedido
    df = df.loc[df['Cod_Producto'] == id_producto]
    
    # Devuelve dataframe filtrado
    join = dflogic.filterDataframes(df,df2)

    if df.shape[0] != 0:
        return json.loads(join.to_json(orient='records'))
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error" : f"No existe el producto con id {id_producto}."}


@app.get('/categorias')
async def getCategorias():
    '''Devuelve todas las categorias'''
    # Lee dataframes y variables 
    df = df_cat.copy()

    return json.loads(df.to_json(orient='records'))


@app.get("/categoria/{id_categoria}")
async def getProductoByCategory(id_categoria: int, response: Response):
    '''Devuelve los productos bajo cierta categoria'''
    # Lee dataframes
    df = df_og.copy()
    df2 = df2_og.copy()
    # Filtra por la categoria pedida
    df = df.loc[df['Cod_Categoria'] == id_categoria]
    
    # Devuelve dataframe filtrado
    join = dflogic.filterDataframes(df,df2)

    if df.shape[0] != 0:
        return json.loads(join.to_json(orient='records'))
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error" : f"No existe la categoria con id {id_categoria}."}


@app.get('/subcategorias')
async def getSubcategorias():
    '''Devuelve todas las subcategorias'''
    # Lee dataframes y variables 
    df = df_subcat.copy()

    return json.loads(df.to_json(orient='records'))


@app.get("/subcategoria/{id_subcategoria}")
async def getProductoBySubcategory(id_subcategoria: int, response: Response):
    '''Devuelve los productos bajo cierta subcategoria'''
    # Lee dataframes
    df = df_og.copy()
    df2 = df2_og.copy()
    # Filtra por la subcategoria
    df = df.loc[df['Cod_Subcategoria'] == id_subcategoria]
    
    # Devuelve dataframe filtrado
    join = dflogic.filterDataframes(df,df2)
    
    if df.shape[0] != 0:
        return json.loads(join.to_json(orient='records'))
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error" : f"No existe subcategoria con id {id_subcategoria}."}


@app.get("/categoria/{id_categoria}/subcategoria/{id_subcategoria}")
async def getProductoByCategory(id_categoria: int, id_subcategoria: int, response: Response, ignoreEmpty: bool = False):
    '''Devuelve los productos bajo cierta categoria que corresponden a una subcategoria'''
    # Lee dataframes
    df = df_og.copy()

    # Si el query parameter ignoreEmpty es true entonces ignora las sucursales vacias
    if ignoreEmpty:
        df2 = df2_og[df2_og['Stock'] != 0].copy()
    else:
        df2 = df2_og.copy()

    # Filtra por la subcategoria y categoria pedida
    df = df.loc[(df['Cod_Categoria'] == id_categoria) & (df['Cod_Subcategoria'] == id_subcategoria)]
    
    # Devuelve dataframe filtrado
    join = dflogic.filterDataframes(df,df2)

    if df.shape[0] != 0:
        return json.loads(join.to_json(orient='records'))
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error" : f"La subcategoria {id_subcategoria} no pertenece a la categoria {id_categoria}, o alguna de estas dos no existe."}


@app.put('/producto/{id}')
async def create_item(id: int, item: Item, response: Response):
    if item.user == config['user1']['username'] and item.password == config['user1']['password']:
        
        global df2_og
        # Lee dataframes
        df = df_og.copy()
        df2 = df2_og.copy()

        df = df.loc[df['Cod_Producto'] == id]
        df2 = DataframeLogic.stockUpItem(id, item.stock, df2)

        # Actualiza los valores en la base de datos
        with context.cursor() as cursor:
            for index, row in df2.loc[df2['Cod_Producto'] == id].iterrows():
                cursor.execute("""
                    UPDATE Producto_Sucursales
                    SET Stock = ?
                    WHERE Cod_Producto = ? AND Cod_Sucursal = ?""", row['Stock'], id, row['Cod_Sucursal'])

        # Devuelve dataframe filtrado
        join = dflogic.filterDataframes(df,df2)

        df2_og = df2
        #guardo en otro container para no sobreescribir el anterior
        df2.to_csv(f'abfs://{datalake_container2}@{datalake_account_name}.dfs.core.windows.net/Producto_Sucursales.csv',storage_options = {'account_key': datalake_account_access_key} ,index=False)

        return json.loads(join.to_json(orient='records'))
    
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message":"El usuario o la contraseña no son validos"}
