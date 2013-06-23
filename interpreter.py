import sys
import time
import re

def seperate(file):
    """Split into program and functions lists"""

    program, functions = [], []
    for line in file:
        if line[:2] == '##':
            program.append(line)
        elif line[2:4] == '->':
            functions.append(line)
    return program, functions

def organise_prog(program):
    """Split program lines imto list of commands"""
    new = [0 for i in program]
    for i, line in enumerate(program):
        new[i] = [i[:2] for i in line.split(',')]
    return new

def organise_funcs(functions):
    """Spilt functions into name and command"""
    functions = {i[:2]: i[5:] for i in functions}

    for key, function in functions.items():
        comment = False
        for i, char in enumerate(function):
            if char == '/':
                if not comment:
                    comment = i
                else:
                    functions[key] = functions[key][:comment]
            else:
                comment = False

        while functions[key][-1:] == ' ':
            functions[key] = functions[key][:-1]

    return functions

def rep(program, functions, out):
    """Report the program and functions"""
    out.output(str(program) + ' ' + str(functions))

def move_coords(direction, y, x):
    """Adjusts y and x in direction""" 
    if direction == 'N':
        y -= 1
    elif direction == 'E':
        x += 1
    elif direction == 'S':
        y += 1
    elif direction == 'W':
        x -= 1
    return y, x

def opp_direction(direction):
    """Returns the direction opposite to the one specified"""
    if direction == 'N':
        return 'S'
    elif direction == 'E':
        return 'W'
    elif direction == 'S':
        return 'N'
    elif direction == 'W':
        return 'E'
    else:
        return None

def move_car(car, instuction):
    """Moves the car with an instruction"""
    if instuction == '%L':
        car.set_direction('W')
    elif instuction == '%R':
        car.set_direction('E')
    elif instuction == '%U':
        car.set_direction('N')
    elif instuction == '%D':
        car.set_direction('S')

def fatal_error(error):
    """Prints the error and exits the program"""
    print('Fatal Error: '+error)
    sys.exit()
def error(error, out):
    """Prints the error"""
    out.output('Error: '+error)


class Output(object):
    """Holds the output"""
    def __init__(self, continuous=False):
        self._out = ''
        self._continuous = continuous

    def __str__(self):
        return self._out

    def output(self, string):
        self._out += '\n'+str(string)
        if self._continuous:
            print(string)
        

class Maze(object):
    """Holds and processes the maze"""
    
    def __init__(self, program, functions, output):
        self._program = program
        self._functions = functions
        self._output = output
        if not len(self._cars) == 1:
            fatal_error('Invalid car in program.')
        else:
            pass

    def __str__(self):
        string = ''
        for row in self._program:
            for cell in row:
                string += str(cell)
            string += '\n'
        return string

    @property
    def running(self):
        if len(self._cars) > 0:
            return True
        else:
            return False

    @property
    def _cars(self):
        no = 0
        cars = []
        for y, row in enumerate(self._program):
            for x, cell in enumerate(row):
                if cell == '^^':
                    self._program[y][x] = Car(y, x, '..')
                if isinstance(self._program[y][x], Car):
                    no += 1
                    cars.append(self._program[y][x])
        return tuple(cars)

    def car_frames(self):
        cars = self._cars
        for car in cars:
            car.frame()

    def _move_cars(self):
        cars = self._cars
        for car in cars:
            if car.hold == 0:
                y, x = car.postion

                directions = ['N', 'E', 'S', 'W']
                # Move current direction to front
                directions.remove(car.direction)
                directions.insert(0, car.direction)
                # Move current backwards direction to back
                opp = opp_direction(car.direction)
                directions.remove(opp)
                directions.append(opp)

                if car.cell == '<>':
                    directions = ['E', 'W']
                for direction in directions:
                    yN, xN = move_coords(direction, y, x)

                    # If the new coords match allow traversing
                    reg1 = re.compile(r'[0-9]{2}')
                    reg2 = re.compile(r'[A-Z]{2}')
                    if (self._program[yN][xN] in ('..', '<>', '()', '>>', 
                                                  '<<', '--', '%L', '%R', 
                                                  '%U', '%D', '**') or
                        not reg1.match(self._program[yN][xN]) is None or
                        not reg2.match(self._program[yN][xN]) is None):

                        # Move Car into new pos, leaving old pos with orig value.
                        old = car.cell
                        new = self._program[yN][xN]

                        self._program[yN][xN] = car
                        self._program[y][x] = old

                        car.set_cell(new)
                        car.move(direction)

                        # If generating a new car, set direction opposite and move
                        if self._program[y][x] == '<>':
                            new_car_direction = opp_direction(direction)
                            yN, xN = move_coords(new_car_direction, y, x)
                            if (self._program[yN][xN] in ('..', '<>', '()', 
                                                          '>>', '<<', '--', 
                                                          '%L', '%R', '%U',
                                                           '%D', '**') or
                                not reg1.match(self._program[yN][xN]) is None or
                                not reg2.match(self._program[yN][xN]) is None):

                                self._program[yN][xN] = Car(yN, xN, 
                                                            self._program[yN][xN],
                                                            car, 
                                                            new_car_direction)
                            else:
                                fatal_error('Invalid program: No space for new car.')

                        break # Skip all other directions, as we used this one.

    def _run_commands(self):
        """"""
        signal = False
        is_function = False
        reg1 = re.compile(r'[0-9]{2}')
        reg2 = re.compile(r'[A-Z]{2}')
        cars = self._cars
        for car in cars:
            y, x = car.postion

            move_car(car, car.cell) # Moves the car if car.cell is a direction
            if not reg1.match(car.cell) is None:
                if car.hold == 0:
                    car.set_hold(car.cell)
            elif car.cell == '()':
                self._program[y][x] = car.cell
            elif car.cell == '>>':
                self._output.output(car.value)
            elif car.cell == '<<':
                car.set_value(input('>'))
            elif car.cell == '--':
                car.set_cell('##')
            elif car.cell == '**':
                signal = True
            elif not reg2.match(car.cell) is None: # If it's a function
                is_function = True

        if is_function == True:
            for car in cars:
                if not reg2.match(car.cell) is None: # If it's a function
                    try:
                        function = self._functions[car.cell]
                    except KeyError:
                        function = False
                        error('Function undeclared.', self._output)
                    
                    if function:
                        if function[:1] == '=':
                            if function[1:2] == '"':
                                car.set_value(function[2:-1])
                            else:
                                car.set_value(function[1:])
                        elif function[:2] == '-=':
                            try:
                                int(function[2:])
                                int_ = True
                            except ValueError:
                                int_ = False
                            if int_:
                                try:
                                    car.set_value(int(int(car.value)-int(function[2:])))
                                except TypeError:
                                    error('Can\'t subtract from non-integer.', self._output)
                            else:
                                error('Can\'t subtract non-integer.', self._output)
                        elif function[:2] == '+=':
                            try:
                                int(function[2:])
                                int_ = True
                            except ValueError:
                                int_ = False
                            if int_:
                                try:
                                    car.set_value(int(int(car.value)+int(function[2:])))
                                except TypeError:
                                    error('Can\'t add to non-integer.', self._output)
                            else:
                                error('Can\'t add non-integer.', self._output)
                        elif function[:2] == '*=':
                            try:
                                int(function[2:])
                                int_ = True
                            except ValueError:
                                int_ = False
                            if int_:
                                try:
                                    car.set_value(int(int(car.value)*int(function[2:])))
                                except TypeError:
                                    error('Can\'t multiply non-integer.', self._output)
                            else:
                                error('Can\'t multiply by non-integer.', self._output)
                        elif function[:2] == '/=':
                            try:
                                int(function[2:])
                                int_ = True
                            except ValueError:
                                int_ = False
                            if int_:
                                try:
                                    car.set_value(int(int(car.value)/int(function[2:])))
                                except TypeError:
                                    error('Can\'t divide non-integer', self._output)
                            else:
                                error('Can\'t divide by non-integer', self._output)
                        
                        elif function[:2] == 'IF':
                            if 'THEN' in function and 'ELSE' in function:
                                comparition = False
                                if function[3:5] == '**':
                                    if signal:
                                        comparition = True
                                elif function[3:5] == '<=':
                                    i = 0
                                    val = ''
                                    char = ''
                                    while not char == ' ':
                                        char = function[5+i:6+i]
                                        val += char
                                        i += 1
                                    val = val[:-1]
                                    try:
                                        if int(car.value) <= int(val):
                                            comparition = True
                                    except ValueError:
                                        error('Can\'t compare string.', self._output)
                                elif function[3:5] == '==':
                                    i = 0
                                    val = ''
                                    char = ''
                                    while not char == ' ':
                                        char = function[5+i:6+i]
                                        val += char
                                        i += 1
                                    val = val[:-1]
                                    try:
                                        if int(car.value) == int(val):
                                            comparition = True
                                    except ValueError:
                                        error('Can\'t compare string.', self._output)
                                elif function[3:5] == '>=':
                                    i = 0
                                    val = ''
                                    char = ''
                                    while not char == ' ':
                                        char = function[5+i:6+i]
                                        val += char
                                        i += 1
                                    val = val[:-1]
                                    try:
                                        if int(car.value) >= int(val):
                                            comparition = True
                                    except ValueError:
                                        error('Can\'t compare string.', self._output)
                                elif function[3:4] == '>':
                                    i = 0
                                    val = ''
                                    char = ''
                                    while not char == ' ':
                                        char = function[4+i:5+i]
                                        val += char
                                        i += 1
                                    val = val[:-1]
                                    try:
                                        if int(car.value) > int(val):
                                            comparition = True
                                    except ValueError:
                                        error('Can\'t compare string.', self._output)
                                elif function[3:4] == '<':
                                    i = 0
                                    val = ''
                                    char = ''
                                    while not char == ' ':
                                        char = function[4+i:5+i]
                                        val += char
                                        i += 1
                                    val = val[:-1]
                                    try:
                                        if int(car.value) < int(val):
                                            comparition = True
                                    except ValueError:
                                        error('Can\'t compare string.', self._output)
                                else:
                                    error('Condition not recognised.', self._output)

                                then_pos = function.find('THEN')
                                else_pos = function.find('ELSE')
                                if comparition:
                                    command = function[then_pos+5:else_pos].strip()
                                else:
                                    command = function[else_pos+5:].strip()
                                
                                move_car(car, command)

                            else:
                                error('Invalid IF statement: Missing THEN or ELSE')

    def frame(self):
        """Updates the maze by one frame"""
        self._move_cars()
        self._run_commands()


class Car(object):
    """Holds information about a Car"""
    
    def __init__(self, y, x, cell, car=None, direction='S'):
        self._y = y
        self._x = x
        self._direction = direction
        self._cell = cell
        self._hold = 0
        if car is None:
            self._value = 0
        else:
            self._value = car.value

    def __str__(self):
        len_ = len(str(self._value))
        if len_ == 1:
            return '0'+str(self._value)
        elif len_ == 0:
            return '00'
        elif len_ > 2:
            return str(self._value)[:2]
        else:
            return str(self._value)

    def frame(self):
        if self._hold > 0:
            self._hold -= 1

    @property
    def value(self):
        return self._value
    def set_value(self, value):
        self._value = value

    @property
    def hold(self):
        return self._hold
    def set_hold(self, hold):
        self._hold = int(hold)

    @property
    def cell(self):
        return self._cell
    def set_cell(self, cell):
        self._cell = cell

    def move(self, direction):
        self._y, self._x = move_coords(direction, self._y, self._x)
        self._direction = direction
    @property
    def postion(self):
        return (self._y, self._x)
    @property
    def direction(self):
        return self._direction
    def set_direction(self, direction):
        self._direction = direction
        
def main():
    try:
        if sys.argv[2] == '-c':
            continuous = True
        else:
            continuous = False
    except IndexError:
        continuous = False

    if continuous:
        maze_out = True
    else:
        try:
            if sys.argv[2] == '-o':
                maze_out = True
            else:
                maze_out = False
        except IndexError:
            maze_out = False

    output = Output(continuous)

    program_file = open(sys.argv[1], 'r').read()
    program_file = program_file.split('\n')[:-1]
    
    program, functions = seperate(program_file)

    program = organise_prog(program)
    functions = organise_funcs(functions)

    maze = Maze(program, functions, output)

    FPS = 8
    i = 0
    while maze.running:
        i += 1
        if maze_out and i > 0:
            print(('\n'*80) + str(maze))
            time.sleep(1/FPS)
        maze.car_frames()
        maze.frame()
    if maze_out:
        print(maze)
    print(output)

if __name__ == '__main__':
    main()