# Functions for creating various glacier data plots.

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from icetools import metrics as met
import ruptures as rpt

# Design parameters
attr_units = {'lengths'         : 'km',
              'areas'           : '$km^2$',
              'termareas'       : '$km^2$',
              'interplengths'   : 'km',
              'interpareas'     : '$km^2$',
              'interptermareas' : '$km^2$'}

attr_names = {'lengths'         : 'Length',
              'areas'           : 'Area',
              'termareas'       : 'Terminus Area',
              'interplengths'   : 'Interpolated Length',
              'interpareas'     : 'Interpolated Area',
              'interptermareas' : 'Interpolated Terminus Area'}

default_color = 'mediumblue'
default_cmap = 'viridis'


# Plot design management
def designProperties(ax, graph):
    """Set standardized figure properties"""
    # Line and marker properties
    linewidth = 1
    markersize = 4
    if type(graph) == matplotlib.lines.Line2D:
        graph.set_zorder(5)
        graph.set_linewidth(linewidth)
        graph.set_markersize(markersize)
    
    # Text properties
    titlesize = 14
    labelsize = 12
    ticklabelsize = 10
    legendsize = 10
    ax.axes.title.set_fontsize(titlesize)
    ax.xaxis.label.set_fontsize(labelsize)
    ax.yaxis.label.set_fontsize(labelsize)
    ax.tick_params(labelsize=ticklabelsize)
    if ax.get_legend() != None:
        ax.legend(fontsize=legendsize)

    # Other properties
    ax.grid(color='lightgray')
    ax.axhline(linewidth=1.0, color='black')
    ax.set_axisbelow(True)

def getGlacierColors(GIDS):
    glacier_cmap = matplotlib.cm.get_cmap('rainbow', len(GIDS))
    glacier_colors = {key: glacier_cmap(key) for key in sorted(dict.fromkeys(GIDS))}
    return glacier_colors

def checkAttribute(attr):
    attribute_types = ['lengths',
                       'areas',
                       'termareas',
                       'interplengths',
                       'interpareas',
                       'interptermareas']
    if attr not in attribute_types:
        raise ValueError('Invalid attribute type. Expected one of: {}'.format(
            attribute_types))

def alignYScale(ax1, ax2):
    ax1min, ax1max = ax1.get_ylim()
    ax2min, ax2max = ax2.get_ylim()
    axmin = min(ax1min, ax2min)
    axmax = max(ax1max, ax2max)
    ax1.set_ylim(axmin, axmax)
    ax2.set_ylim(axmin, axmax)

def annotateBars(ax, anno, x, y):
    for i in range(len(anno)):
        sign = y[i]/abs(y[i])
        ax.annotate(anno[i],
                    xy=(x[i], 0),#y[i]), 
                    xytext = (0, -sign * 8),
                    textcoords = 'offset points',
                    ha='center', va='center')

def pickTimeLabel(glacier, attr):
    checkAttribute(attr)
    if attr in ['lengths', 'areas', 'termareas']:
        # time = glacier.dates
        timelabel = 'Date'
    elif attr in ['interplengths', 'interpareas', 'interptermareas']:
        # time = glacier.datayears
        timelabel = 'Hydrological Year'
    return timelabel


# Plots

def annualObservations(ax, glaciers, years, show_firstyear=True):
    for g in glaciers:
        glacier = glaciers[g]
        
        graph1 = plt.scatter([glacier.gid]*len(glacier.hydroyears), \
            glacier.hydroyears, \
            c=glacier.daysofhydroyear, cmap='twilight_shifted')
        graph2 = plt.scatter([glacier.gid]*len(glacier.interpyears), \
            glacier.interpyears, \
            edgecolors='gray', facecolors='none')
        
        designProperties(ax, graph1)
        designProperties(ax, graph2)
    
    if show_firstyear:
        first_full_year = met.firstFullYear(glaciers)
        ax.axhline(y=first_full_year, linewidth=3.0, color='red', zorder=0.5)
    
    ax.set_title('Observation Time Series')
    ax.set_xlabel('Glacier ID')
    ax.set_ylabel('Hydrological Year')
    plt.ylim(bottom=years[0]-1, top=years[-1]+1)

    # Add colorbar with season labels
    cbar = plt.colorbar(graph1, label='Day of hydrological year', \
        values=list(range(0, 366)))
    tick_locator = matplotlib.ticker.LinearLocator(numticks=9)
    cbar.locator = tick_locator
    cbar.update_ticks()
    cbar.ax.set_yticklabels(
        ['', 'Autumn', '', 'Winter', '', 'Spring', '', 'Summer', ''], 
        rotation=90, verticalalignment='center')
    
    designProperties(ax, graph1)
    designProperties(ax, graph2)


def dateObservations(ax, glaciers, gids, years, xax='glacier'):
    count = 0
    for g in glaciers:
        glacier = glaciers[g]
        if xax == 'glacier':
            graph = plt.scatter([count]*len(glacier.dates), glacier.dates, c=default_color)
        elif xax == 'date':
            graph = plt.scatter(glacier.dates, [count]*len(glacier.dates), c=default_color)
        designProperties(ax, graph)
        count = count+1

    ax.set_title('Observation Time Series')
    if xax == 'glacier':
        ax.set_xlabel('Glacier ID')
        ax.set_ylabel('Date')
        plt.xticks(range(len(gids)), gids, rotation=90)
        plt.ylim(bottom=pd.to_datetime(years[0], format='%Y'), \
                top=pd.to_datetime(years[-1]+1, format='%Y'))
    elif xax == 'date':
        ax.set_xlabel('Date')
        ax.set_ylabel('Glacier ID')
        plt.yticks(range(len(gids)), gids)
        plt.xlim(left=pd.to_datetime(years[0], format='%Y'), \
                 right=pd.to_datetime(years[-1]+1, format='%Y'))

    designProperties(ax, graph)
        

def cumulativeChange(ax, glacier, attr, startdate=None, enddate=None):
    checkAttribute(attr)
    
    cumulative_attr, cumulative_dates, _ = glacier.cumulativeChange(
        attr, startdate, enddate)
    graph, = ax.plot(cumulative_dates, cumulative_attr, \
        'o-', color=default_color)

    ax.set_title('{}: {} Change'.format(glacier.name, attr_names[attr]))
    ax.set_xlabel(pickTimeLabel(glacier, attr))
    ax.set_ylabel('Cumulative {} Change ({})'.format(
        attr_names[attr], attr_units[attr]))
    xleft = pd.to_datetime(cumulative_dates.iloc[0].year-1, format='%Y')
    xright = pd.to_datetime(cumulative_dates.iloc[-1].year+1, format='%Y')
    plt.xlim(left=xleft, right=xright)
    designProperties(ax, graph)


def differentialChange(ax, glacier, attr, startdate=None, enddate=None):
    checkAttribute(attr)

    attrs, dates = glacier.filterDates(attr, startdate, enddate)
    diff_attrs = attrs.diff()

    graph = ax.bar(dates, diff_attrs, width=75, color=default_color)
    ax.set_title('{}: {} Change Between Measurements'.format(
        glacier.name, attr_names[attr]))
    ax.set_xlabel(pickTimeLabel(glacier, attr))
    ax.set_ylabel('{} Change ({})'.format(attr_names[attr], attr_units[attr]))
    xleft = pd.to_datetime(dates.iloc[0].year-1, format='%Y')
    xright = pd.to_datetime(dates.iloc[-1].year+1, format='%Y')
    plt.xlim(left=xleft, right=xright)
    designProperties(ax, graph)


def decadalChange(ax, glacier, attr, startdecades):
    checkAttribute(attr)

    startdecades = pd.to_datetime(startdecades)
    net_decadal_change = pd.Series(dtype='float64')
    decade_labels = []
    bar_annotations = []
    for startyear in startdecades:
        endyear = met.addDecade(startyear)
        cumul_decadal_change, _, num_obsv = glacier.cumulativeChange(
            attr, startyear, endyear)
        net_decadal_change.loc[midyear] = cumul_decadal_change.iloc[-1]
        midyear = endyear.year - 4
        decade_labels.append('{}-{}'.format(startyear.year, startyear.year+9))
        bar_annotations.append('{} obsv'.format(num_obsv))
    
    rects = ax.bar(net_decadal_change.index.values, net_decadal_change.values,\
        width=5, color=default_color)
    annotateBars(ax, bar_annotations, \
        net_decadal_change.index.values, net_decadal_change.values)
    ax.set_title('{}: Decadal {} Change'.format(glacier.name, attr_names[attr]))
    ax.set_xlabel('Decade')
    ax.set_ylabel('Net {} Change ({})'.format(
        attr_names[attr], attr_units[attr]))
    xtlocs = ax.get_xticks()
    ax.set_xticks(xtlocs+5)
    ax.set_xticklabels(decade_labels)
    if max(ax.get_ylim()) == 0.0:
        yrange, _ = ax.get_ylim()
        ax.set_ylim(top=abs(0.05*yrange))

    designProperties(ax, rects)
    ax.set_axisbelow(True)
    ax.grid(axis='x')


def changeSummary(ax, glaciers, attr, glacier_colors, startdate=None, enddate=None):
    checkAttribute(attr)

    for g in glaciers:
        glacier = glaciers[g]
        cumulative_attr, cumulative_dates, _ = glacier.cumulativeChange(
            attr, startdate, enddate)
        graph, = ax.plot(cumulative_dates, cumulative_attr, color=default_color, alpha=0.3)
        if len(glaciers) < 8:
            graph.set_color(glacier_colors[glacier.gid])
            graph.set_alpha(0.9)
            graph.set_label(glacier.name)
        # xleft = pd.to_datetime(cumulative_dates.iloc[0].year-1, format='%Y')
        # xright = pd.to_datetime(cumulative_dates.iloc[-1].year+1, format='%Y')
        # plt.xlim(left=xleft, right=xright)
        designProperties(ax, graph)
    
    ax.set_title('Glacier {} Changes'.format(attr_names[attr]))
    ax.set_xlabel(pickTimeLabel(glacier, attr))
    ax.set_ylabel('Cumulative {} Change ({})'.format(
        attr_names[attr], attr_units[attr]))
    xleft = pd.to_datetime(cumulative_dates.iloc[0].year-1, format='%Y')
    xright = pd.to_datetime(cumulative_dates.iloc[-1].year+1, format='%Y')
    plt.xlim(left=xleft, right=xright)
    if len(glaciers) < 8:
        ax.legend()
    designProperties(ax, graph)


def changeSummaryNorm(ax, glaciers, attr, startdate=None, enddate=None, showmean=True):
    checkAttribute(attr)

    for g in glaciers:
        glacier = glaciers[g]
        scaled_attr, scaled_dates = glacier.normChange(
            attr, startdate, enddate)
        graph, = ax.plot(scaled_dates, scaled_attr, color='dimgray', alpha=0.3)
        designProperties(ax, graph)
    if showmean == True:
        norm_mean, norm_std = met.normChangeStats(glaciers, attr, startdate=startdate, enddate=enddate)
        norm_dates = pd.to_datetime(norm_mean.index, format='%Y')
        ax.plot(norm_dates, norm_mean.values, label='mean +/- std', 
            color=default_color, linewidth=3, zorder=10)
        ax.fill_between(norm_dates, 
            norm_mean.values+norm_std.values, norm_mean.values-norm_std.values, 
            color=default_color, alpha=0.2, zorder=10)  
    
    ax.set_title('Normalized Glacier {} Changes'.format(attr_names[attr]))
    ax.set_xlabel(pickTimeLabel(glacier, attr))
    ax.set_ylabel('Normalized Cumulative {} Change'.format(
        attr_names[attr]))
    xleft = pd.to_datetime(scaled_dates.iloc[0].year-1, format='%Y')
    xright = pd.to_datetime(scaled_dates.iloc[-1].year+1, format='%Y')
    plt.xlim(left=xleft, right=xright)
    # plt.ylim(-0.01, 1.01)
    designProperties(ax, graph)


def showChangePoints(ax, glacier, attr, startdate=None, enddate=None, n_breakpoints=1, method='window'):
    """Plot breakpoints using built-in methods in ruptures package."""
    _, signal, breakpoints = met.changePointDetection(glacier, attr, startdate, enddate, n_breakpoints, method)
    rpt.show.display(signal, breakpoints, figsize=(6, 5))
    plt.show()


def changePointHistogram(ax, glaciers, attr, startdate=None, enddate=None, n_breakpoints=1, method='window', model='l1', wwidth=5, year_bins=None):
    """Plot histogram of breakpoint years for glacier population."""
    checkAttribute(attr)
    population_breakpoint_years = []
    for g in glaciers:
        glacier = glaciers[g]
        breakpoint_dates, _, _ = met.changePointDetection(glacier, attr, startdate=startdate, enddate=enddate, n_breakpoints=n_breakpoints, method=method, model=model, wwidth=wwidth)
        breakpoint_years = [d.year for d in breakpoint_dates]
        # graph = ax.scatter(breakpoint_years, [g]*len(breakpoint_years), color=default_color)
        # designProperties(ax, graph)
        population_breakpoint_years.extend(breakpoint_years)
    graph = ax.hist(population_breakpoint_years, bins=year_bins, rwidth=0.8, color=default_color)
    
    ax.set_title('Glacier {} Change Points'.format(attr_names[attr]))
    ax.set_xlabel('Year')
    ax.set_ylabel('Glacier ID')#'Count')
    designProperties(ax, graph)
        

