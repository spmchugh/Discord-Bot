from sqlalchemy import ForeignKey, String, Integer, CHAR, Column, Boolean
import sqlalchemy.orm

Base = sqlalchemy.orm.declarative_base()

class User(Base):
    __tablename__ = "users"

    # Discord identifying information
    discordId = Column("discordId", Integer, primary_key = True)
    serverId = Column("serverId", Integer, primary_key = True)
    
    # Riot Games identifying information
    username = Column("username", String)
    tag = Column("tag", String)
    puuid = Column("puuid", String)
    summonerId = Column("summonerId", String)
    accountId = Column("accountId", String)

    # User rank information
    rank = Column("rank", String)
    division = Column("division", String)
    lp = Column("lp", Integer)
    value = Column("value", Integer)
    currRank = Column("currRank", Boolean, primary_key = True)

    def __init__(self, discordId, serverId, username, tag, puuid,
                 summonerId, accountId, rank, division, lp, value, currRank):
        self.discordId = discordId
        self.serverId = serverId
        self.username = username
        self.tag = tag
        self.puuid = puuid
        self.summonerId = summonerId
        self.accountId = accountId
        self.rank = rank
        self.division = division
        self.lp = lp
        self.value = value
        self.currRank = currRank