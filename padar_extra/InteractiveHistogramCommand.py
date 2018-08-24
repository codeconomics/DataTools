import InteractiveHistogram
import click as cli

@cli.command()
@cli.argument('annotations', type=cli.Path(exists=True))
@cli.argument('all_testing', type=cli.Path(exists=True))
@cli.argument('all_training', type=cli.Path(exists=True))
def gen_interactive_histograms(annotations, all_testing, all_training):
    InteractiveHistogram.gen_interactive_histograms(annotations=annotations, 
                                                all_testing=all_testing, 
                                                all_training=all_training)


if __name__ == '__main__':
    gen_interactive_histograms()
               