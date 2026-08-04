package com.panpan.aibusinessservice.service;

import com.panpan.aibusinessservice.dto.CurrentUserView;
import com.panpan.aibusinessservice.dto.TicketListItemView;
import java.util.List;

public interface TicketQueryService {
    List<TicketListItemView> listVisibleTickets(CurrentUserView currentUser);
}
