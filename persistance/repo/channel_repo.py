import sqlite3
from typing import Union

from persistance.entitiy.channel_entity import ChannelEntity


class ChannelRepo(object):
    def __init__(self):
        self.connection = sqlite3.connect("rusniya_db")
        self.cursor = self.connection.cursor()

    def __mapRow(self, row: tuple) -> Union[ChannelEntity, None]:
        channel = ChannelEntity(row[0], row[2], row[1], row[3])
        return channel

    def findAll(self):
        result = []
        rows = self.cursor.execute(
            """
            select * from channel
            order by subscribers desc;
            """
        )
        if len(rows) == 0:
            return
        for row in rows:
            result.append(self.__mapRow(row))

    def findAllByApprovedAndActive(self, approved: int):
        result = []
        rows = self.cursor.execute(
            """
            select * from channel
            where approved = {0}
            and active = 1
            order by subscribers desc;
            """.format(approved)
        )
        rows = rows.fetchall()
        if len(rows) == 0:
            return
        for row in rows:
            result.append(self.__mapRow(row))
        return result

    def findById(self, id: int) -> Union[ChannelEntity, None]:
        result = self.cursor.execute(
            """
            select * from channel
            where id = {0}
            """.format(id)
        )
        row = result.fetchone()
        if row is None:
            return
        return self.__mapRow(row)

    def findByLink(self, link: str) -> Union[ChannelEntity, None]:
        result = self.cursor.execute(
            """
            select * from channel
            where link = '{0}'
            """.format(link)
        )
        row = result.fetchone()
        if row is None:
            return
        return self.__mapRow(row)

    def save(self, channel: ChannelEntity):
        print(channel.link + " saved")
        self.cursor.execute(
            """
            insert into channel (id, link, subscribers, active, approved)
            values ({0}, '{1}', {2}, {3}, {4})
            """.format(channel.id, channel.link, channel.subscribers, channel.active, channel.approved)
        )
        self.connection.commit()

    def updateApproveByLink(self, link: str, approved: int):
        print(link + " approved" if approved == 1 else " not approved")
        self.cursor.execute(
            """
            update channel
            set approved = {0}
            where link = '{1}';
            """.format(approved, link)
        )
        self.connection.commit()
