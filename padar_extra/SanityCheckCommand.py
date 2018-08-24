import click
import SanityCheck

@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.argument('config_path', type=click.Path(exists=True))
@click.option('--totalreport', is_flag=True, default=False)
@click.option('--pid')
def sanity_check(root_path, config_path, totalreport, pid):
    SanityCheck.sanity_check(root_path=root_path,
                            config_path=config_path,
                            totalreport=totalreport,
                            pid=pid)

if __name__ == '__main__':
    sanity_check()