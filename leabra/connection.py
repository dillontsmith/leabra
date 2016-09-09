from .unit import Unit
import numpy as np


class Link:
    """A link between two units. Simple, non active class."""

    def __init__(self, pre_unit, post_unit, w0):
        self.pre  = pre_unit
        self.post = post_unit
        self.wt   = w0


class Connection:
    """Connection between layers"""

    def __init__(self, pre_layer, post_layer, spec=None):
        """
        Parameters:
            pre_layer   the layer sending its activity.
            post_layer  the layer receiving the activity.
        """
        self.pre  = pre_layer
        self.post = post_layer
        self.links = []
        self.spec = spec
        if self.spec is None:
            self.spec = ConnectionSpec()
        assert (self.spec.lrule is None or
                self.spec.lrule.lower() in self.spec.legal_lrule)

        self.spec.projection_init(self)

        post_layer.connections.append(self)

        


    @property
    def weights(self):
        """Return a matrix of the links weights"""
        if self.spec.proj.lower() == '1to1':
            return np.array([[link.w for link in self.links]])
        else:  # proj == 'full'
            W = np.zeros((len(self.pre.units), len(self.post.units)))  # weight matrix
            link_it = iter(self.links)  # link iterator
            for i, pre_u in enumerate(self.pre.units):
                for j, post_u in enumerate(self.post.units):
                    W[i, j] = next(link_it).wt
            return W





    def learn(self):
        if self.spec.lrule is not None:
            getattr(self, self.spec.lrule + '_lrule')()
        for link in self.links:
            link.wt = max(0.0, min(1.0, link.wt)) # clipping weights after change


    def delta_lrule(self):
        """Delta learning rule.

        Presumably at the end of the plus phase, compares difference between the
        current activity of the post-unit (allegedly representing the target
        activity) with its activity at the end of the minus phase (stored in
        `act_m`). The weights are then modified in proportion to this difference,
        the current pre-unit activity (credit attribution) and the learning rate.
        """
        for link in self.links:
            dwt = self.spec.lrate * (link.post.act - link.post.act_m) * link.pre.act  # eq. A8
            link.wt += dwt

    def xcal_lrule(self):
        """XCAL learning rule"""
        raise NotImplementedError

    def cycle(self):
        self.spec.cycle(self)

class ConnectionSpec:

    legal_lrule = None, 'delta', 'xcal' # available values for self.lrule
    legal_proj  = 'full', '1to1'        #              ... for self.proj

    def __init__(self, **kwargs):
        """Connnection parameters"""
        self.st    = 1.0     # connection strength
        self.force = False   # activity are set directly in the post_layer
        self.inhib = False   # if True, inhibitory connection
        self.w0    = 1.0     # intial weights
        self.proj  = 'full'  # connection pattern between units.
                             # Can be 'Full' or '1to1'. In the latter case,
                             # the layers must have the same size.
        self.lrule = None    # the learning rule to use. Possible values are
                             # 'delta', 'xcal' and None.
        self.lrate = 0.01    # learning rate

        for key, value in kwargs.items():
            setattr(self, key, value)

    def cycle(self, connection):
        """Transmit activity."""
        for link in connection.links:
            scaled_act = self.st * link.wt * link.pre.act
            link.post.add_excitatory(scaled_act, forced=self.force)
        

    def _full_projection(self, connection):
        # creating unit-to-unit links
        connection.links = []
        for pre_u in connection.pre.units:
            for post_u in connection.post.units:
                connection.links.append(Link(pre_u, post_u, self.w0))
        

    def _1to1_projection(self, connection):
        # creating unit-to-unit links
        connection.links = []
        assert connection.pre.size == connection.post.size
        for pre_u, post_u in zip(connection.pre.units, connection.post.units):
            connection.links.append(Link(pre_u, post_u, self.w0))
        

    def projection_init(self, connection):
        if self.proj == 'full':
            self._full_projection(connection)
        if self.proj == '1to1':
            self._1to1_project(connection)