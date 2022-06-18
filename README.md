# homework4

## Description:

Cryptocurrency exchange where users can buy and sell currency.

### Create venv:
    make venv

### Run tests:
    make test

### Run linters:
    make lint

### Run formatters:
    make format

### Init database
    make init_db

### Run server
    make up

## Api:

```http
POST /currency/add
```
Adds a new cryptocurrency with the specified name if it doesn't exist.

#### Body

```JSON
{
 "name": "your_currency"
}
```

```http
GET /currency/<currency_name>
```
Returns extended information about the specified cryptocurrency if it exists.
Note that ```currency_name``` parameter must be in lowercase.

```http
GET /currency/all
```

Returns information about all cryptocurrencies.

```http
POST /user/registration
```

#### Body

```JSON
{
 "name": "your_name"
}
```

Adds a user to the exchange.

```http
GET /user/<user_name>
```
Returns information about the specified user if it exists.

```http
GET /user/<user_name>/operations?limit=10&page=1
```
| Parameter | Type  | Description                                  |
|:----------|:------|:---------------------------------------------|
| `limit`   | `int` | **Required**. Number of operations per page. |
| `page`    | `int` | **Required**. Page number (starts with 0).   |

Returns paginated list of user operations.

```http
POST /trade
```

```JSON
{
  "currency_name": "currency_name",
  "user_name": "user_name",
  "operation": "buy/sell",
  "currency_amount": 1.1,
  "exchange_rate": 43.21
}
```

Performs the specified operation for the specified user. 