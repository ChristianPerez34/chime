from base64 import b64encode
import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from inflection import humanize
from pandas import to_datetime
from pandas import DataFrame
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.deps.db import get_async_session
from app.models.submission import Submission
from app.schemas.token import (
    Submission as SubmissionSchema,
    SubmitToken,
    TokenLookup,
    TokenLookupItem,
)
from calendar import monthrange
from random import shuffle
from aiocoingecko import AsyncCoinGeckoAPISession
from plotly.graph_objects import Candlestick, Figure
from plotly.io import to_image


router = APIRouter(prefix="/tokens")


@router.get("/", status_code=200)
async def token_lookup(
    symbol: str = "", session: AsyncSession = Depends(get_async_session)
) -> TokenLookup:
    async with AsyncCoinGeckoAPISession() as coin_gecko:
        coins_list = [
            TokenLookupItem(**coin) for coin in await coin_gecko.get_coins_list()
        ]

        if symbol:
            coins_list = [coin for coin in coins_list if coin.symbol == symbol]
    return TokenLookup(data=coins_list)


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
        raise HTTPException(status_code=400, detail="Submission already exists")
    submission = Submission(**submission_in.dict())
    session.add(submission)
    await session.commit()
    return SubmissionSchema.from_orm(submission)


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
    submissions = [
        SubmitToken(
            name=submission.name,
            symbol=submission.symbol,
            description=submission.description,
        )
        for submission in query.all()
    ]
    shuffle(submissions)

    response = submissions[:10]
    return response


@router.get("/price/{token_id}", status_code=200)
async def token_price(
    token_id: str,
):
    token_id = token_id.lower()

    async with AsyncCoinGeckoAPISession() as coin_gecko:
        token = await coin_gecko.get_coin_by_id(coin_id=token_id)
    return token


@router.get("/price/{token_id}/chart", status_code=200)
async def chart(token_id: str, days: str = "max"):
    symbol = token_id.lower()

    async with AsyncCoinGeckoAPISession() as coin_gecko:
        name = humanize(token_id)
        market_data = await coin_gecko.get_coin_ohlc_by_id(
            coin_id=token_id, vs_currency="usd", days=days
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

    return {"name": name, "image": image_base64}


@router.get("/trending", status_code=200)
async def trending():
    async with AsyncCoinGeckoAPISession() as coin_gecko:
        trending = await coin_gecko.get_search_trending()

    return {"data": [coin["item"] for coin in trending["coins"]]}
