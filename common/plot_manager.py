import logging
import matplotlib.pyplot as plt


class PlotManager:
    def __init__(self, max_elements, enabled=True   ):
        self.logger = logging.getLogger('plot_manager')

        self.is_enabled = enabled

        self.plot_lines = {}
        self.plot_data = {}

        if self.is_enabled:
            plt.ion()
            self.fig = plt.figure()
        else:
            plt.ioff()

        self.max_elements = max_elements
        self.latest_tick = {}

        self.subplots = {}
        self.subplot_lines = {}

        self.texts = {}

        self.logger.debug("Plot manager initialized")

    def add_line(self, subplot_id, line_id, x_data=[], y_data=[], line_width=1):
        if not self.is_enabled:
            return
        if line_id in self.plot_data:
            self.logger.warning('Plot line %s already exists' % line_id)
            return
        if subplot_id not in self.subplots:
            self.logger.warning('Subplot %s does not exist' % subplot_id)
            return
        self.plot_data[line_id] = [x_data, y_data]
        self.plot_lines[line_id], = self.subplots[subplot_id].plot(
            x_data,
            y_data,
            linewidth=line_width
        )
        self.subplot_lines[subplot_id].append(line_id)
        self.latest_tick[line_id] = max(x_data)
        self.update_lims()
        self.refresh()

    def update_line(self, line_id, x_val, new_y_val):
        if not self.is_enabled:
            return
        if line_id not in self.plot_data:
            self.logger.error('Plot line %s not present in plot manager' % line_id)
            return
        if x_val < 0:
            self.logger.error('Invalid x value: %d' % x_val)
            return
        if x_val not in self.plot_data[line_id][0]:
            x_data = self.plot_data[line_id][0]
            for i in range(0, x_data):
                if x_data[i] < x_val:
                    continue
                x_data = x_data[:i] + x_val + x_data[i:]
                break
            self.plot_data[line_id][0] = x_data
        self.plot_data[line_id][1][self.plot_data[line_id][0].index(x_val)] = new_y_val
        self.plot_lines[line_id].set_ydata(self.plot_data[line_id][1])
        self.update_lims()
        self.refresh()

    def update_lims(self):
        if not self.is_enabled:
            return
        for subplot_id in self.subplots:
            ymin, ymax = 1e10, -1
            for line_id in self.subplot_lines[subplot_id]:
                self.subplots[subplot_id].set_xlim([
                    max(0, self.latest_tick[line_id]-self.max_elements),
                    max(self.subplots[subplot_id].get_xlim()[1], self.latest_tick[line_id])
                ])
                ymin = min(ymin, min(self.plot_data[line_id][1][-self.max_elements:]))
                ymax = max(ymax, max(self.plot_data[line_id][1][-self.max_elements:]))
            self.subplots[subplot_id].set_ylim([ymin, ymax])

    def add_subplot(self, subplot_id, layout):
        if not self.is_enabled:
            return
        self.subplots[subplot_id] = plt.subplot(layout)
        self.subplot_lines[subplot_id] = []
        self.refresh()

    def append_datapoint(self, subplot_id, x_value, y_data):
        self.logger.debug("Appending (%r, %r)" % (x_value, y_data))
        if not self.is_enabled:
            return
        if subplot_id not in self.subplots:
            self.logger.warning('Subplot %s does not exist' % subplot_id)
            return
        for line_id in y_data:
            if x_value <= self.latest_tick[line_id]:
                self.logger.error('Can only append to the end of data: latest=%d, x=%d' % (self.latest_tick[line_id], x_value))
                return
            self.latest_tick[line_id] = x_value
            self.plot_data[line_id][0].append(x_value)
            self.plot_data[line_id][1].append(y_data[line_id])
            self.plot_lines[line_id].set_xdata(self.plot_data[line_id][0])
            self.plot_lines[line_id].set_ydata(self.plot_data[line_id][1])
        self.update_lims()
        self.refresh()

    def set_subplot_title(self, subplot_id, subplot_title):
        if not self.is_enabled:
            return
        if subplot_id not in self.subplots:
            self.logger.warning('Subplot %s does not exist' % subplot_id)
            return
        self.subplots[subplot_id].set_title(subplot_title)
        self.refresh()

    def refresh(self):
        if not self.is_enabled:
            return
        plt.draw()
        plt.pause(0.01)

    def add_text(self, text_id, text, x=0, y=0, font_size=14):
        if not self.is_enabled:
            return
        if text_id in self.texts:
            self.logger.error('Text %s already exists' % text_id)
            return
        self.texts[text_id] = plt.gcf().text(x, y, text, fontsize=font_size)

    def update_text(self, text_id, new_text):
        if not self.is_enabled:
            return
        if text_id not in self.texts:
            self.logger.error('Text %s does not exist (list: %r)' % (text_id, [t for t in self.texts]))
            return
        self.texts[text_id].set_text(new_text)

    def freeze_plot(self):
        if self.is_enabled:
            plt.ioff()
            plt.show()
