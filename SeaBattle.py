from random import randint, choice
from string import ascii_uppercase


class SeaBattleError(Exception):
    """Общий класс ошибок игры"""


class ShipMoveError(SeaBattleError):
    """Ошибка движения корабля"""


class IndexBoardError(SeaBattleError):
    """Ошибка координаты поля"""


class ShootError(SeaBattleError):
    """Ошибка выстрела"""


class Cell:
    def __init__(self, ship):
        self.ship = ship
        self._value = True

    def hit(self):
        self._value = False
        self.ship.hurt()

    def __str__(self):
        return '▢' if self._value else '▩'

    def __bool__(self):
        return self._value


class Ship:
    def __init__(self, length, tp=1, x=None, y=None):
        self._length = length
        self._tp = tp
        self._x = x
        self._y = y

        self._is_move = True
        self._cells = [Cell(self) for _ in range(length)]

    def set_start_coords(self, x, y):
        self._x, self._y = x, y

    @property
    def get_start_coords(self):
        return self._x, self._y

    @property
    def get_finish_coords(self):
        width, height = (self._length, 1) if self._tp == 1 else (1, self._length)
        return self._x + width, self._y + height

    def hurt(self):
        if self._is_move:
            self._is_move = False

    def move(self, direction):
        if not self._is_move:
            raise ShipMoveError

        if self._tp == 1:
            self._x += direction
        else:
            self._y += direction

    def is_collide(self, ship):
        x2, y2 = self.get_finish_coords
        x1_ship, y1_ship = ship.get_start_coords
        x2_ship, y2_ship = ship.get_finish_coords
        return self._x <= x2_ship and x2 >= x1_ship and self._y <= y2_ship and y2 >= y1_ship

    def is_out_board(self, size):
        return any(map(lambda x: not 0 <= x < size, (*self.get_start_coords, *self.get_finish_coords)))

    def __getitem__(self, item):
        return self._cells[item]

    def __setitem__(self, key, value):
        self._cells[key] = value

    def __len__(self):
        return self._length

    def __bool__(self):
        return any(self._cells)

    def __repr__(self):
        return f'Ship(length={self._length})'


class DefenderMoveShip:
    def __init__(self, ship):
        self.__ship = ship
        self.__x, self.__y = ship.get_start_coords

    def __enter__(self):
        return self.__ship

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.__ship.set_start_coords(self.__x, self.__y)


class Board:
    _NUMS_SHIPS = (4, 1), (3, 2), (2, 3), (1, 4)

    def __init__(self, size=10):
        self._size = size
        self._ships = []
        self.create()

    def create(self):
        ships = [Ship(length, tp=randint(1, 2)) for length, nums in self._NUMS_SHIPS for _ in range(nums)]
        for ship in ships:
            self._placement_ship(ship)

    def _placement_ship(self, ship):
        while True:
            x, y = randint(0, self._size - 1), randint(0, self._size - 1)
            ship.set_start_coords(x, y)
            if not self._check_location_ship(ship):
                self._ships.append(ship)
                return

    @property
    def get_ships(self):
        return self._ships

    def show(self):
        print('X|' + '|'.join(map(str, range(1, 11))))
        print('\n'.join(f'{ascii_uppercase[i]}|' + '|'.join(map(str, row)) for i, row in enumerate(self.get_board)))
        print('-' * 30)

    @property
    def get_board(self):
        res = [['*'] * self._size for _ in range(self._size)]
        for ship in self._ships:
            x1, y1 = ship.get_start_coords
            x2, y2 = ship.get_finish_coords
            i = 0
            for y in range(y1, y2):
                for x in range(x1, x2):
                    res[y][x] = ship[i]
                    i += 1
        return res

    def _check_location_ship(self, ship):
        return ship.is_out_board(self._size) or any(ship.is_collide(other) for other in self._ships if other != ship)

    def _move_ship(self, ship, direction):
        ship.move(direction)

        if self._check_location_ship(ship):
            raise ShipMoveError

    def move_ships(self):
        for s in self._ships:
            direction = choice((1, -1))
            try:
                with DefenderMoveShip(s) as ship:
                    self._move_ship(ship, direction)
            except SeaBattleError:
                try:
                    with DefenderMoveShip(s) as ship:
                        self._move_ship(ship, -direction)
                except SeaBattleError:
                    pass

    def __getitem__(self, item: tuple):
        row, col = item
        return self.get_board[row][col]

    def __bool__(self):
        return any(self._ships)

    def hit(self, y, x):
        if any(map(lambda p: not 0 <= p < self._size, (x, y))):
            raise IndexBoardError('Координаты не могут превышать размер поля!')
        target = self.get_board[y][x]
        if isinstance(target, Cell):
            if not target:
                raise ShootError('В это поле уже было попадание!')
            target.hit()
            if target.ship:
                print('Ранен!')
            else:
                print('Убит!')
            return True

        print('Мимо!')
        return False


class Player:
    def __init__(self):
        self.board = Board()

    def __bool__(self):
        return bool(self.board)

    def shoot(self, player):
        raise NotImplementedError


class AI(Player):
    def shoot(self, player):
        x, y = randint(0, 9), randint(0, 9)
        try:
            res = player.board.hit(x, y)
            print(f'AI наносит выстрел по координатам {x}, {y}')
            return res
        except ShootError:
            self.shoot(player)


class Human(Player):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def shoot(self, player):
        try:
            y, x = input('Введите две координаты выстрела сперва букву, затем цифру без пробела: ').upper()
            if y not in ascii_uppercase or not x.isdigit():
                raise ValueError
            return player.board.hit(ascii_uppercase.index(y), int(x) - 1)
        except ValueError:
            print('Неверный ввод координаты!')
        except (IndexBoardError, ShootError) as e:
            print(e)
        self.shoot(player)


class SeaBattle:
    def __init__(self):
        self._human = Human('Player')
        self._ai = AI()

        self._turn = None

    def __bool__(self):
        return all((self._human, self._ai))

    def _move_ships(self):
        for board in self._ai.board, self._human.board:
            board.move_ships()

    def _player_turn(self, player: Player):
        other_player = self._ai if player == self._human else self._human
        other_player.board.show()
        return player.shoot(other_player)

    def _change_turn(self):
        if self._turn == self._human:
            self._turn = self._ai
        else:
            self._turn = self._human
            self._move_ships()

    def start(self):
        self._turn = self._human

        while self:
            if not self._player_turn(self._turn):
                self._change_turn()

        if not self._ai:
            print('Игрок победил!')
        else:
            print('ПК победил!')


if __name__ == '__main__':
    game = SeaBattle()
    game.start()
