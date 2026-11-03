with tab_safety:
    st.subheader("👥 Union Safety Rep & Union Safety Committee")
    st.markdown("<p style='color: #94a3b8; font-family: monospace;'>Official Plant Safety Committee Directory & Plant FAP Contacts (Rev. 8/31/2026)</p>", unsafe_allow_html=True)
    
    safety_data = [
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Sean Els - Safety Committee Chair - USR, Training", "Clock #": "001-002", "Turn": "Days", "Crew": "", "Phone": "(330) 495-7614", "Email": "sean.l.els@metallus.com (Work ext. 2913)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Scott Mathie - USR, Training", "Clock #": "001-800", "Turn": "Days", "Crew": "", "Phone": "(330) 412-6508", "Email": "robert.s.mathie@metallus.com (Work ext. 3967)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Curtis Green - USR, Compliance", "Clock #": "001-502", "Turn": "Days", "Crew": "", "Phone": "(330) 949-5148", "Email": "curtis.e.green@metallus.com (Work ext. 4716)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Tim Johnson - USR, Plant & Shops", "Clock #": "001-003", "Turn": "Days", "Crew": "", "Phone": "(330) 933-0824", "Email": "timothy.j.johnson@metallus.com (Work ext. 5026)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Chad Steiner - Machine Shop", "Clock #": "181-062", "Turn": "Days", "Crew": "", "Phone": "(740) 391-0555", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Dave Ramsey - Finishing", "Clock #": "133-022", "Turn": "4", "Crew": "B", "Phone": "(330) 265-7701", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Brad Holston - Equipment Rebuild", "Clock #": "181-001", "Turn": "Days", "Crew": "", "Phone": "(330) 347-1188", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Steve Carlisle - Weld Shop", "Clock #": "181-505", "Turn": "Days", "Crew": "", "Phone": "(330) 340-0876", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Seth McKenzie - Finishing", "Clock #": "133-029", "Turn": "4", "Crew": "C", "Phone": "(330) 232-5536", "Email": ""},

        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "John Lidderdale - USR, Steelmaking", "Clock #": "001-801", "Turn": "Days", "Crew": "", "Phone": "(330) 209-1254", "Email": "john.t.lidderdale@metallus.com (Work ext. 4682)"},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Mike Henderson - USR, Steel Processing", "Clock #": "001-804", "Turn": "Days", "Crew": "", "Phone": "(330) 428-2503", "Email": "michael.l.henderson@metallus.com (Work ext. 7360)"},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Chuck Fetrow - BC", "Clock #": "250-084", "Turn": "3", "Crew": "C", "Phone": "(330) 488-4765", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Mike Kiser - Mech. Maint. Rolling Mill", "Clock #": "282-012", "Turn": "4", "Crew": "B", "Phone": "(330) 934-1190", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Jeff Thomas - Rolling Mill", "Clock #": "282-040", "Turn": "4", "Crew": "B", "Phone": "(330) 446-8285", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Adam Holland - Caster", "Clock #": "227-025", "Turn": "Days", "Crew": "", "Phone": "(330) 904-8489", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Daryl Smith - BC", "Clock #": "250-025", "Turn": "3", "Crew": "C", "Phone": "(330) 418-6012", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Alan Tack - Chem Lab", "Clock #": "008-003", "Turn": "4", "Crew": "B", "Phone": "(330) 323-5315", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Alex Rue - EAF", "Clock #": "218-054", "Turn": "4", "Crew": "C", "Phone": "(330) 606-5792", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Brandon Bartrug - EAF", "Clock #": "218-058", "Turn": "Days", "Crew": "", "Phone": "(740) 391-0109", "Email": ""},

        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Brock McDevitt - USR, Tube Mills & Thermal Treat", "Clock #": "001-500", "Turn": "Days", "Crew": "", "Phone": "(330) 432-0705", "Email": "brock.a.mcdevitt@metallus.com (Work ext. 4249)"},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Shawn Lindner - USR, Finishing & Logistics", "Clock #": "001-501", "Turn": "Days", "Crew": "", "Phone": "(330) 575-4435", "Email": "shawn.lindner@metallus.com (Work ext. 5083)"},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Carrie Holland - IFL", "Clock #": "752-408", "Turn": "4", "Crew": "D", "Phone": "(330) 933-6620", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Mike Kemp - 5 Tube Mill", "Clock #": "750-041", "Turn": "3", "Crew": "A", "Phone": "(330) 268-6375", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Jason Ensinger - 3TM", "Clock #": "750-306", "Turn": "2", "Crew": "H", "Phone": "(330) 956-0178", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Ed Smith - IFL", "Clock #": "752-002", "Turn": "Days", "Crew": "", "Phone": "(330) 949-7623", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Jon Burdge - Logistics, Shipping", "Clock #": "190-078", "Turn": "Days", "Crew": "", "Phone": "(330) 224-2778", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Marty Gugov - Logistics, Shipping", "Clock #": "190-019", "Turn": "2", "Crew": "B", "Phone": "(330) 437-5967", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Ken Rayburn - Logistics, Shipping", "Clock #": "190-036", "Turn": "4", "Crew": "C", "Phone": "(330) 809-3183", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Alex Hunt - Quench/Temper", "Clock #": "756-025", "Turn": "3", "Crew": "B", "Phone": "(330) 413-4839", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Joe Plott - Thermal Treat, Islands", "Clock #": "185-527", "Turn": "4", "Crew": "C", "Phone": "(330) 428-1716", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Marc Armstead - Met Lab", "Clock #": "007-021", "Turn": "2", "Crew": "Midnights", "Phone": "(330) 844-6363", "Email": ""},

        {"Plant / Location": "FAP Leads - Plant", "Name / Area": "Carrie Holland - GSP, IFL", "Clock #": "752-408", "Turn": "Days", "Crew": "", "Phone": "(330) 933-6620", "Email": ""},
        {"Plant / Location": "FAP Leads - Plant", "Name / Area": "Chuck Fetrow - FSP, BC", "Clock #": "250-084", "Turn": "3", "Crew": "A", "Phone": "(330) 488-4765", "Email": ""},
        {"Plant / Location": "FAP Leads - Plant", "Name / Area": "Greg Smith - HSP, Machine Shop", "Clock #": "181-025", "Turn": "Days", "Crew": "", "Phone": "(330) 437-8015", "Email": ""}
    ]
    
    df_safety = pd.DataFrame(safety_data)
    search_term = st.text_input("🔍 Search Directory by Name, Plant, or Area:", "")
    if search_term:
        mask = df_safety.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        df_filtered = df_safety[mask]
    else:
        df_filtered = df_safety
        
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
