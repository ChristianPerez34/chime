from asyncio import sleep
from base64 import b64encode
import datetime
from typing import List
from fastapi import APIRouter, Depends
from inflection import humanize
from pandas import to_datetime
from pandas import DataFrame
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.deps.db import get_async_session
from app.models.submission import Submission
from app.schemas.token import Submission as SubmissionSchema, SubmitToken
from fastapi.responses import JSONResponse
from calendar import monthrange
from random import shuffle
from aiocoingecko import AsyncCoinGeckoAPISession
from plotly.graph_objects import Candlestick, Figure
from plotly.io import to_image


router = APIRouter(prefix="/tokens")


@router.post("/monthly/submit", status_code=201)
async def submit_token(
    submission_in: SubmitToken,
    session: AsyncSession = Depends(get_async_session),
) -> SubmissionSchema:
    today = datetime.date.today()
    first_day_of_month = datetime.date(today.year, today.month, 1)
    past_submission = await session.scalar(
        select(Submission).filter(
            and_(
                Submission.symbol == submission_in.symbol,
                Submission.name == submission_in.name,
                Submission.created_at >= first_day_of_month,
            )
        )
    )

    if past_submission:
        error_message = {"detail": "Submission already exists"}
        return JSONResponse(content=error_message, status_code=404)
    submission = Submission(**submission_in.dict())
    session.add(submission)
    await session.commit()
    return submission


@router.get("/monthly/draw", status_code=200)
async def monthly_draw(
    session: AsyncSession = Depends(get_async_session),
) -> List[SubmitToken]:
    today = datetime.date.today()
    first_day_of_month = datetime.date(today.year, today.month, 1)
    last_day_of_month = (
        first_day_of_month
        + datetime.timedelta(days=monthrange(today.year, today.month)[1])
        - datetime.timedelta(days=1)
    )

    query = await session.scalars(
        select(Submission).filter(
            Submission.created_at.between(first_day_of_month, last_day_of_month),
        )
    )
    submissions = query.all()
    shuffle(submissions)

    response = [
        SubmitToken(
            name=submission.name,
            symbol=submission.symbol,
            description=submission.description,
        )
        for submission in submissions[:10]
    ]
    return response


@router.get("/price/{symbol}", status_code=200)
async def token_price(
    symbol: str,
):
    symbol = symbol.lower()
    response = []
    async with AsyncCoinGeckoAPISession() as coin_gecko:
        coins_list = await coin_gecko.get_coins_list()
        coins_list = [coin for coin in coins_list if coin["symbol"] == symbol]

        for coin in coins_list:
            token = await coin_gecko.get_coin_by_id(coin_id=coin["id"])
            response.append(token)
    return {"data": response}


@router.get("/price/{symbol}/chart", status_code=200)
async def chart(symbol: str, days: str = "max"):
    symbol = symbol.lower()
    response = []
    async with AsyncCoinGeckoAPISession() as coin_gecko:
        coins_list = await coin_gecko.get_coins_list()
        coins_list = [coin for coin in coins_list if coin["symbol"] == symbol]

        for coin in coins_list:
            name = humanize(coin["id"])
            market_data = await coin_gecko.get_coin_ohlc_by_id(
                coin_id=coin["id"], vs_currency="usd", days=days
            )
            dataframe = DataFrame(
                market_data, columns=["date", "open", "high", "low", "Close"]
            )
            dataframe.date = to_datetime(dataframe.date, unit="ms")
            fig = Figure(
                data=[
                    Candlestick(
                        x=dataframe["date"],
                        open=dataframe["open"],
                        high=dataframe["high"],
                        low=dataframe["low"],
                        close=dataframe["Close"],
                    ),
                ]
            )
            fig.update_layout(
                title=f"Candlestick graph for {name} ({symbol})",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                xaxis_rangeslider_visible=False,
            )

            fig.update_yaxes(tickprefix="$")
            image_bytes = to_image(fig=fig, format="png")
            image_base64 = b64encode(image_bytes).decode("ascii")

            response.append({"name": name, "image": image_base64})
            await sleep(0.5)
    return {"data": response}


@router.get("/trending", status_code=200)
async def trending():
    async with AsyncCoinGeckoAPISession() as coin_gecko:
        trending = await coin_gecko.get_search_trending()

    return {"data": [coin["item"] for coin in trending["coins"]]}
