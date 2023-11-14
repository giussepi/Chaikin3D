# -*- coding: utf-8 -*-
""" chaikin3d.py """

from chaikin3d.managers import ChaikinMGR


def main():
    """Main function"""
    # reading options from command line ###################################
    # python code
    poly = ChaikinMGR()(plot=False)
    # print(type(poly))
    # shell call
    # python chaikin3d.py -i my_obj.obj -cg 4 -cc 4 -p evolution -oe first

    # reading options from string #########################################
    # python code
    # poly = ChaikinMGR(cmd_args='-i my_obj.obj -cg 4 -cc 4 -p evolution -oe first')(plot=False)
    # shell call
    # python chaikin3d.py


if __name__ == "__main__":
    main()
