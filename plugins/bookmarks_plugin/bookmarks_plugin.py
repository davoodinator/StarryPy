import os
import errno
import json

from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
from packets import Packets, fly_ship_write
from utility_functions import build_packet


class Bookmarks(SimpleCommandPlugin):
    """
    Plugin that allows defining planets as personal bookmarks you can /goto to.
    """
    name = 'bookmarks_plugin'
    depends = ['command_plugin', 'player_manager_plugin']
    commands = ['bookmark_add', 'bookmark_del', 'goto']

    def activate(self):
        super(Bookmarks, self).activate()
        self.player_manager = self.plugins[
            'player_manager_plugin'
        ].player_manager
        self.verify_path('./config/bookmarks')

    @permissions(UserLevels.GUEST)
    def bookmark_add(self, name):
        """
        Bookmarks a planet for fast warp routes.
        Syntax: /bookmark_add (name)
        """
        filename = os.path.join(
            'config', 'bookmarks', '{}.json'.format(self.protocol.player.uuid)
        )
        try:
            with open(filename) as f:
                self.bookmarks = json.load(f)
        except:
            self.bookmarks = []

        name = ' '.join(name).strip().strip('\t')
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship

        if on_ship:
            self.protocol.send_chat_message('You need to be on a planet!')
            return
        if not name:
            warps = []
            for warp in self.bookmarks:
                if warps != '':
                    warps.append(warp[1])
            warpnames = '^green;,^yellow; '.join(warps)
            if warpnames == '':
                warpnames = '^gray;(none)^green;'
            self.protocol.send_chat_message(self.bookmark_add.__doc__)
            self.protocol.send_chat_message(
                'Please, provide a valid bookmark name!\n'
                'Bookmarks: ^yellow;{}'.format(warpnames)
            )
            return

        for warp in self.bookmarks:
            if warp[0] == planet:
                self.protocol.send_chat_message(
                    'The planet you\'re on is already '
                    'bookmarked: ^yellow;{}'.format(warp[1])
                )
                return
            if warp[1] == name:
                self.protocol.send_chat_message(
                    'Bookmark with that name already exists!'
                )
                return
        self.bookmarks.append([planet, name])
        self.protocol.send_chat_message(
            'Bookmark ^yellow;{}^green; added.'.format(name)
        )
        self.savebms()

    @permissions(UserLevels.GUEST)
    def bookmark_del(self, name):
        """
        Removes current planet from bookmarks.
        Syntax: /bookmark_del (name)
        """
        filename = os.path.join(
            'config', 'bookmarks', '{}.json'.format(self.protocol.player.uuid)
        )
        try:
            with open(filename) as f:
                self.bookmarks = json.load(f)
        except:
            self.bookmarks = []
        name = ' '.join(name).strip().strip('\t')
        if not name:
            warps = []
            for warp in self.bookmarks:
                if warp:
                    warps.append(warp[1])
            warpnames = '^green;,^yellow; '.join(warps)
            if warpnames == '':
                warpnames = '^gray;(none)^green;'
            self.protocol.send_chat_message(self.bookmark_del.__doc__)
            self.protocol.send_chat_message(
                'Please, provide a valid bookmark name!\n'
                'Bookmarks: ^yellow;{}'.format(warpnames)
            )
            return

        for warp in self.bookmarks:
            if warp[1] == name:
                self.bookmarks.remove(warp)
                self.protocol.send_chat_message(
                    'Bookmark ^yellow;%s^green; removed.'.format(name)
                )
                self.savebms()
                return
        self.protocol.send_chat_message(
            'There is no bookmark named: ^yellow;{}'.format(name)
        )

    @permissions(UserLevels.GUEST)
    def goto(self, name):
        """
        Warps your ship to a previously bookmarked planet.
        Syntax: /goto [name] *omit name for a list of bookmarks
        """
        filename = os.path.join(
            'config', 'bookmarks', '{}.json'.format(self.protocol.player.uuid)
        )
        try:
            with open(filename) as f:
                self.bookmarks = json.load(f)
        except:
            self.bookmarks = []
        name = ' '.join(name).strip().strip('\t')
        if name:
            warps = []
            for warp in self.bookmarks:
                if warp:
                    warps.append(warp[1])
            warpnames = '^green;,^yellow; '.join(warps)
            if warpnames == '':
                warpnames = '^gray;(none)^green;'
            self.protocol.send_chat_message(self.goto.__doc__)
            self.protocol.send_chat_message(
                'Bookmarks: ^yellow;{}'.format(warpnames)
            )
            return

        on_ship = self.protocol.player.on_ship
        if not on_ship:
            self.protocol.send_chat_message('You need to be on a ship!')
            return

        for warp in self.bookmarks:
            if warp[1] == name:
                x, y, z, planet, satellite = map(int, warp[0].split(':'))
                warp_packet = build_packet(
                    Packets.FLY_SHIP,
                    fly_ship_write(
                        x=x,
                        y=y,
                        z=z,
                        planet=planet,
                        satellite=satellite
                    )
                )
                self.protocol.client_protocol.transport.write(warp_packet)
                self.protocol.send_chat_message(
                    'Warp drive engaged! Warping to ^yellow;{}^green;.'.format(
                        name
                    )
                )
                return
        self.protocol.send_chat_message(
            'There is no bookmark named: ^yellow;%s'.format(name)
        )

    def savebms(self):
        filename = os.path.join(
            'config', 'bookmarks', '{}.json'.format(self.protocol.player.uuid)
        )
        try:
            with open(filename, 'wb') as f:
                json.dump(self.bookmarks, f)
        except:
            self.logger.exception('Couldn\'t save bookmarks.')
            raise

    def verify_path(self, path):
        """
        Helper function to make sure path exists, and create if it doesn't.
        """
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
