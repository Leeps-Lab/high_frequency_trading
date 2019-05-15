from createMarketEvents import createMarketEvents
import os

root_path = os.getcwd()
investor_file = 'random_order_inputs_set_2.csv'
jump_file = 'my_jump.csv'
period_length = 240
lambda_j = 1/3 # freq of value changes
lambda_i = 3 # freq of orders
price_origin = 100
sig_jump = 0.5
muI = sig_jump
sigI = 2 * sig_jump
lambda_tif = 5
tif_random_flag = False
csv_flag = True


if __name__ == '__main__':
    createMarketEvents(
        os.getcwd(),
        investor_file,
        jump_file,
        period_length,
        lambda_j,
        lambda_i,
        price_origin,
        sig_jump,
        muI,
        sigI,
        lambda_tif,
        tif_random_flag,
        csv_flag)