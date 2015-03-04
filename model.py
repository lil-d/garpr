import trueskill


class TrueskillRating(object):
    def __init__(self, trueskill_rating=None):
        if trueskill_rating:
            self.trueskill_rating = trueskill_rating
        else:
            self.trueskill_rating = trueskill.Rating()

    def __str__(self):
        return "(%.3f, %.3f)" % (self.trueskill_rating.mu, self.trueskill_rating.sigma)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.trueskill_rating == other.trueskill_rating

    def __ne__(self, other):
        return not self == other

    def get_json_dict(self):
        json_dict = {}

        json_dict['mu'] = self.trueskill_rating.mu
        json_dict['sigma'] = self.trueskill_rating.sigma

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(trueskill.Rating(mu=json_dict['mu'], sigma=json_dict['sigma']))


class MatchResult(object):
    def __init__(self, winner=None, loser=None):
        '''
        :param winner: ObjectId
        :param loser: ObjectId
        '''
        self.winner = winner
        self.loser = loser

    def __str__(self):
        return "%s > %s" % (self.winner, self.loser)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.winner == other.winner and \
               self.loser == other.loser

    def __ne__(self, other):
        return not self == other

    def contains_players(self, player1, player2):
        return (self.winner == player1 and self.loser == player2) or \
               (self.winner == player2 and self.loser == player1)

    def contains_player(self, player_id):
        return self.winner == player_id or self.loser == player_id

    def did_player_win(self, player_id):
        return self.winner == player_id

    def get_opposing_player_id(self, player_id):
        if self.winner == player_id:
            return self.loser
        elif self.loser == player_id:
            return self.winner
        else:
            return None

    def get_json_dict(self):
        json_dict = {}

        json_dict['winner'] = self.winner
        json_dict['loser'] = self.loser

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(winner=json_dict['winner'], loser=json_dict['loser'])

'''
Object definition of a player history.
Tied to a tournament id.
'''
class PlayerHistory(object):
    def __init__(self, player, tournament, id=None):
        '''
        :param player: Player object
        :param tournament: Tournament object
        :param id: ObjectId, auto-generated when inserted into db
        '''
        self.id = id
        self.player_id = player.id
        self.player_name = player.name
        self.ratings = player.ratings
        self.regions = player.regions
        self.tournament_id = tournament.id
        self.created_on = tournament.date
        self.rankings

    def __str__(self):
        return "%s %s %s %s %s %s %s" % (
            self.id,
            self.player_id,
            self.player_name,
            {reg: str(rat) for reg, rat in self.ratings.iteritems()},
            self.tournament_id,
            self.regions,
            self.created_on
        )

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.id == other.id and \
               self.player_id == other.player_id and \
               self.player_name == other.player_name and \
               self.ratings == other.ratings and \
               self.regions == other.regions and \
               self.created_on == other.created_on and \
               self.tournament_id == other.tourament.rating

    def __ne__(self, other):
        return not self == other

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['player_name'] = self.player_name
        json_dict['player_id'] = self.player_id
        json_dict['ratings'] = {region: rating.get_json_dict() for region, rating in self.ratings.iteritems()}
        json_dict['regions'] = self.regions
        json_dict['created_on'] = self.created_on
        json_dict['tournament_id'] = self.tournament_id

        return json_dict


class Player(object):
    def __init__(self, name, aliases, ratings, regions, id=None):
        # TODO force aliases to lowercase
        '''
        :param name: String
        :param aliases:  List of Strings
        :param ratings:  dict[region: String] -> rating, where rating is a dict[region: String] -> float
        :param regions: List of Strings
        :param id: ObjectId, auto-generated when you insert into mongo
        '''
        self.id = id
        self.name = name
        self.aliases = aliases
        self.ratings = ratings
        self.regions = regions

    @classmethod
    def create_with_default_values(cls, name, region):
        return cls(name, [name.lower()], {}, [region])

    def __str__(self):
        return "%s %s %s %s %s" % (
            self.id,
            self.name,
            {reg: str(rat) for reg, rat in self.ratings.iteritems()},
            self.aliases,
            self.regions)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.id == other.id and \
               self.name == other.name and \
               set(self.aliases) == set(other.aliases) and \
               self.ratings == other.ratings and \
               self.regions == other.regions

    def __ne__(self, other):
        return not self == other

    def merge_with_player(self, player):
        aliases_set = set(self.aliases)
        regions_set = set(self.regions)

        aliases_set.update(set(player.aliases))
        regions_set.update(set(player.regions))

        self.aliases = list(aliases_set)
        self.regions = list(regions_set)

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['name'] = self.name
        json_dict['aliases'] = self.aliases
        json_dict['ratings'] = {region: rating.get_json_dict() for region, rating in self.ratings.iteritems()}
        json_dict['regions'] = self.regions

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
            json_dict['name'],
            json_dict['aliases'],
            {region: TrueskillRating.from_json(rating_dict) for region, rating_dict in
             json_dict['ratings'].iteritems()},
            json_dict['regions'],
            id=json_dict['_id'] if '_id' in json_dict else None)


class Tournament(object):
    def __init__(self, type, raw, date, name, players, matches, regions, id=None):
        '''
        :param type: string, either "tio" or "challonge"
        :param raw: for tio, this is an xml string. for challonge its a dict from string --> string
        :param date: datetime
        :param name: string
        :param players: list of ObjectIDs
        :param matches:  list of MatchResults
        :param regions: list of string
        :param id: ObjectID, autogenerated by mongo during insert
        '''
        self.id = id
        self.type = type
        self.raw = raw
        self.date = date
        self.name = name
        self.matches = matches
        self.regions = regions
        self.players = players

    def replace_player(self, player_to_remove=None, player_to_add=None):
        # TODO edge cases with this
        # TODO the player being added cannot play himself in any match
        if player_to_remove is None or player_to_add is None:
            raise TypeError("player_to_remove and player_to_add cannot be None!")

        player_to_remove_id = player_to_remove.id
        player_to_add_id = player_to_add.id

        if not player_to_remove_id in self.players:
            print ("Player with id %s is not in this tournament. Ignoring." % player_to_remove.id)
            return

        self.players.remove(player_to_remove_id)
        self.players.append(player_to_add_id)

        for match in self.matches:
            if match.winner == player_to_remove_id:
                match.winner = player_to_add_id

            if match.loser == player_to_remove_id:
                match.loser = player_to_add_id

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['type'] = self.type
        json_dict['raw'] = self.raw
        json_dict['date'] = self.date
        json_dict['name'] = self.name
        json_dict['players'] = self.players
        json_dict['matches'] = [m.get_json_dict() for m in self.matches]
        json_dict['regions'] = self.regions

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
            json_dict['type'],
            json_dict['raw'],
            json_dict['date'],
            json_dict['name'],
            json_dict['players'],
            [MatchResult.from_json(m) for m in json_dict['matches']],
            json_dict['regions'],
            id=json_dict['_id'] if '_id' in json_dict else None)

    @classmethod
    def from_pending_tournament(cls, pending_tournament):
        # alias_to_id_map is a map from player alias (string) -> player id (ObjectId)
        def _get_player_id_from_map_or_throw(alias_to_id_map, alias):
            player_id = alias_to_id_map[alias]
            if player_id is None:
                raise Exception('Alias %s has no ID in map\n: %s' % (alias, alias_to_id_map))
            else:
                return player_id

        alias_to_id_map = pending_tournament.alias_to_id_map

        # the players and matches returned from the scraper use player aliases
        # we need to convert these to player IDs
        players = [_get_player_id_from_map_or_throw(alias_to_id_map, p) for p in pending_tournament.players]
        for m in pending_tournament.matches:
            m.winner = _get_player_id_from_map_or_throw(alias_to_id_map, m.winner)
            m.loser = _get_player_id_from_map_or_throw(alias_to_id_map, m.loser)
        return cls(
            pending_tournament.type,
            pending_tournament.raw,
            pending_tournament.date,
            pending_tournament.name,
            players,
            pending_tournament.matches,
            pending_tournament.regions)

    @classmethod
    def from_scraper(cls, type, scraper, alias_to_id_map, region_id):
        pending_tournament = PendingTournament.from_scraper(type, scraper, region_id)
        pending_tournament.alias_to_id_map = alias_to_id_map

        return Tournament.from_pending_tournament(pending_tournament)


class PendingTournament(object):
    '''Same as a Tournament, except it uses aliases for players instead of ids.
       Used during tournament import, before alias are mapped to player ids.'''

    def __init__(self, type, raw, date, name, players, matches, regions, alias_to_id_map={}, id=None):
        self.id = id
        self.type = type
        self.raw = raw
        self.date = date
        self.name = name
        self.matches = matches
        self.regions = regions
        self.alias_to_id_map = alias_to_id_map

        # player aliases, not ids!
        self.players = players

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['type'] = self.type
        json_dict['raw'] = self.raw
        json_dict['date'] = self.date
        json_dict['name'] = self.name
        json_dict['players'] = self.players
        json_dict['matches'] = [m.get_json_dict() for m in self.matches]
        json_dict['regions'] = self.regions
        json_dict['alias_to_id_map'] = self.alias_to_id_map

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
            json_dict['type'],
            json_dict['raw'],
            json_dict['date'],
            json_dict['name'],
            json_dict['players'],
            [MatchResult.from_json(m) for m in json_dict['matches']],
            json_dict['regions'],
            json_dict['alias_to_id_map'],
            id=json_dict['_id'] if '_id' in json_dict else None)

    def add_alias_id_mapping(self, alias, _id):
        self.alias_to_id_map[alias] = _id

    def are_all_aliases_mapped(self):
        return set(self.alias_to_id_map.keys()) == set(self.players)

    @classmethod
    def from_scraper(cls, type, scraper, region_id):
        players = scraper.get_players()
        matches = scraper.get_matches()
        regions = [region_id]

        return cls(
            type,
            scraper.get_raw(),
            scraper.get_date(),
            scraper.get_name(),
            players,
            matches,
            regions)


class Ranking(object):
    def __init__(self, region, time, tournaments, ranking, id=None):
        '''
        :param region: string
        :param time: datetime
        :param tournaments: list of ObjectIds
        :param ranking: TODO
        :param id: TODO
        '''
        self.region = region
        self.id = id
        self.time = time
        self.ranking = ranking
        self.tournaments = tournaments

    def get_json_dict(self):
        json_dict = {}

        if self.id:
            json_dict['_id'] = self.id

        json_dict['region'] = self.region
        json_dict['time'] = self.time
        json_dict['tournaments'] = self.tournaments
        json_dict['ranking'] = [r.get_json_dict() for r in self.ranking]

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
            json_dict['region'],
            json_dict['time'],
            json_dict['tournaments'],
            [RankingEntry.from_json(r) for r in json_dict['ranking']],
            id=json_dict['_id'] if '_id' in json_dict else None)


# TODO be explicit about this being a player_id
class RankingEntry(object):
    def __init__(self, rank, player, rating):
        '''
        :param rank: TODO
        :param player: TODO
        :param rating: TODO
        '''
        self.rank = rank
        self.player = player
        self.rating = rating

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.rank == other.rank and \
               self.player == other.player and \
               self.rating == other.rating

    def __ne__(self, other):
        return not self == other

    def get_json_dict(self):
        json_dict = {}

        json_dict['rank'] = self.rank
        json_dict['player'] = self.player
        json_dict['rating'] = self.rating

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
            json_dict['rank'],
            json_dict['player'],
            json_dict['rating'])


class Region(object):
    def __init__(self, id, display_name):
        '''
        :param id: TODO
        :param display_name: TODO
        '''
        self.id = id
        self.display_name = display_name

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.id == other.id and \
               self.display_name == other.display_name

    def __ne__(self, other):
        return not self == other

    def get_json_dict(self):
        json_dict = {}

        json_dict['_id'] = self.id
        json_dict['display_name'] = self.display_name

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
            json_dict['_id'],
            json_dict['display_name'])


class User(object):
    def __init__(self, id, admin_regions, full_name=""):
        self.id = id
        self.full_name = full_name
        self.admin_regions = admin_regions

    def __str__(self):
        return "%s %s %s" % (self.id, self.full_name, self.admin_regions)

    def get_json_dict(self):
        json_dict = {}

        json_dict['_id'] = self.id
        json_dict['full_name'] = self.full_name
        json_dict['admin_regions'] = self.admin_regions

        return json_dict

    @classmethod
    def from_json(cls, json_dict):
        if json_dict == None:
            return None

        return cls(
            json_dict['_id'],
            json_dict['admin_regions'],
            json_dict['full_name'])

