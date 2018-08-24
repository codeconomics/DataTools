import click
import Visualizer
import os

@click.group()
def cli_annotation_feature_grapher():
    pass

@click.group()
def cli_acc_grapher():
    pass

@click.group()
def cli_feature_grapher():
    pass

@cli_annotation_feature_grapher.command()
@click.argument('annotationdata', type=click.Path(exists=True))
@click.option('--featuredata', default=None, help='csv file path of the feature data in mHealth format, if not provided, will not graph features')
@click.option('--path_out', type=click.Path(exists=True), default=os.path.dirname(os.path.realpath(__file__)),
                help='the output path of the graph created, if not provided, will store in the current folder')
@click.option('--non_overlap', is_flag=True, default=False, help='indicating if the annotations have any overlap, if not, will create spectrum graph, ONLY USE IT WHEN NOT GRAPHING FEATURES')
@click.option('--title', default='', help='the title of graph')
@click.option('--feature_index', default=None, help='a list of indexes of features to show in python syntax')
@click.option('--feature_num', default=16, help='number of features')
def annotation_feature_grapher(annotationdata, featuredata, path_out, non_overlap, title, feature_index, feature_num):
    Visualizer.annotation_feature_grapher(annotationdata=annotationdata, 
                            featuredata=featuredata, 
                            path_out=path_out, 
                            non_overlap=non_overlap, 
                            title=title, 
                            feature_index=feature_index,
                            feature_num=feature_num)


@cli_acc_grapher.command()
@click.argument('data', type=click.Path(exists=True))
@click.option('--path_out', type=click.Path(exists=True), default=os.path.dirname(os.path.realpath(__file__)),
                help='the output path of the graph created, if not provided, will store in the current folder')
def acc_grapher(data, path_out):
    Visualizer.acc_grapher(data=data, path_out=path_out, showlegend=True)


@cli_feature_grapher.command()
@click.argument('featuredata', type=click.Path(exists=True))
@click.option('--path_out', type=click.Path(exists=True), default=os.path.dirname(os.path.realpath(__file__)),
                help='the output path of the graph created, if not provided, will store in the current folder')
@click.option('--feature_index', default=None, help='a list of indexes of features to show in python syntax')
@click.option('--feature_num', default=16, help='number of features')
def feature_grapher(featuredata, path_out, feature_index, feature_num):
    Visualizer.feature_grapher(featuredata=featuredata, feature_index=feature_index, showlegend=True, hide_traces=True,
                                path_out=path_out,
                                feature_num=feature_num)


total_comands = click.CommandCollection(sources=[cli_annotation_feature_grapher, cli_acc_grapher, cli_feature_grapher])

if __name__ == '__main__':
    total_comands()