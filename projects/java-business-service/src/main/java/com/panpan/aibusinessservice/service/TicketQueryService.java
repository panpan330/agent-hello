package com.panpan.aibusinessservice.service;

import com.panpan.aibusinessservice.dto.CurrentUserView;
import com.panpan.aibusinessservice.dto.TicketDetailView;
import com.panpan.aibusinessservice.dto.TicketListItemView;
import com.panpan.aibusinessservice.dto.UpdateTicketStatusRequest;
import java.util.List;

public interface TicketQueryService {
    List<TicketListItemView> listVisibleTickets(CurrentUserView currentUser);

    TicketDetailView getVisibleTicket(CurrentUserView currentUser, String ticketId);

    TicketDetailView updateTicketStatus(
            CurrentUserView currentUser,
            String ticketId,
            UpdateTicketStatusRequest request,
            String traceId
    );
}
